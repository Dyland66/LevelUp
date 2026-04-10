from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model to support Student/Parent vs Coach/Teacher roles,
    plus profile fields requested in the spec.
    """

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student/Parent"
        COACH = "COACH", "Coach/Teacher"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        NON_BINARY = "NON_BINARY", "Non-binary"
        PREFER_NOT = "PREFER_NOT", "Prefer not to say"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    # Requested profile fields
    forename = models.CharField(max_length=80, blank=True)
    surname = models.CharField(max_length=80, blank=True)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)

    # Optional extras
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def full_name(self) -> str:
        name = f"{self.forename} {self.surname}".strip()
        return name if name else self.username


class Category(models.Model):
    """
    Grinds / Sports / Music
    """
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name


class Skill(models.Model):
    """
    A specific subject/discipline within a category.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=60)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"


class Area(models.Model):
    """
    Area-based filtering for in-person sessions.
    """
    name = models.CharField(max_length=80, unique=True)

    def __str__(self) -> str:
        return self.name


# -----------------------------------------------------------------
# COACH SUBSCRIPTION
# Coaches must select a subscription plan at signup.
# Currently only "FREE" exists; "PRO" (€59.95/yr) is shown as
# coming soon so the business model is visible to reviewers.
# -----------------------------------------------------------------
class CoachSubscription(models.Model):
    """
    Tracks which subscription tier a coach has chosen.
    Currently FREE is the only active tier; PRO is placeholder
    to demonstrate the intended monetisation model.
    """

    class Tier(models.TextChoices):
        FREE = "FREE", "Free"
        PRO  = "PRO",  "Pro – €59.95/year"

    coach_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="subscription",
        limit_choices_to={"role": User.Role.COACH},
    )
    tier = models.CharField(max_length=10, choices=Tier.choices, default=Tier.FREE)
    started_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.coach_user.username} — {self.get_tier_display()}"


class CoachProfile(models.Model):
    """
    Extra coach-only data.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="coach_profile")

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="coaches")
    teaches = models.ManyToManyField(Skill, blank=True, related_name="coaches")
    travel_areas = models.ManyToManyField(Area, blank=True, related_name="coaches")
    base_location_eircode = models.CharField(max_length=10, blank=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Verified badge — set manually by admin after Garda vetting / document check.
    # Relevant for Leaving Cert grinds where students may be under-18.
    is_verified = models.BooleanField(
        default=False,
        help_text="Manually set by admin after identity/Garda vetting check.",
    )

    def __str__(self) -> str:
        return f"{self.user.full_name()} - {self.category.name}"

    def average_rating(self) -> float | None:
        """
        Returns the average star rating across all completed reviews,
        or None if no reviews exist yet.
        Used on coach cards and profile pages.
        """
        reviews = self.reviews.all()
        if not reviews.exists():
            return None
        total = sum(r.stars for r in reviews)
        return round(total / reviews.count(), 1)

    def review_count(self) -> int:
        return self.reviews.count()


# -----------------------------------------------------------------
# CHILD PROFILE (GDPR Article 8 — parent/guardian accounts)
# A Student/Parent user can create sub-profiles for their children.
# The child's name appears on bookings instead of the parent's.
# No separate login — the parent manages everything.
# -----------------------------------------------------------------
class ChildProfile(models.Model):
    """
    Sub-profile created by a parent/guardian (Student role) for a minor.
    Relevant to GDPR Article 8 — data relating to children requires
    heightened protection and parental consent.
    """
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="child_profiles",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    forename = models.CharField(max_length=80)
    surname  = models.CharField(max_length=80)
    dob      = models.DateField(help_text="Used to confirm the child is a minor (under 18).")
    year_group = models.CharField(
        max_length=40,
        blank=True,
        help_text="e.g. 5th Year, Leaving Cert, Junior Cert",
    )

    def full_name(self) -> str:
        return f"{self.forename} {self.surname}".strip()

    def __str__(self) -> str:
        return f"{self.full_name()} (child of {self.parent.username})"


class SessionSlot(models.Model):
    """
    Slots created by coaches that students can book.
    """

    class Mode(models.TextChoices):
        ONLINE    = "ONLINE",    "Online"
        IN_PERSON = "IN_PERSON", "In person"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED    = "BOOKED",    "Booked"
        CANCELLED = "CANCELLED", "Cancelled"

    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="slots")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="slots")
    mode  = models.CharField(max_length=20, choices=Mode.choices)
    area  = models.ForeignKey(Area, on_delete=models.PROTECT, null=True, blank=True, related_name="slots")
    venue_eircode  = models.CharField(max_length=10, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime   = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start time must be before end time.")

        if self.coach_id and self.skill_id:
            if not self.coach.teaches.filter(pk=self.skill_id).exists():
                raise ValidationError("You can only create sessions for skills you teach.")

        if self.mode == self.Mode.IN_PERSON and self.area is None:
            raise ValidationError("In-person sessions must include an area for filtering.")

        if self.skill_id:
            cat_name = self.skill.category.name.lower()
            if cat_name == "sports":
                if self.mode != self.Mode.IN_PERSON:
                    raise ValidationError("Sports sessions must be in-person.")
                if not self.venue_eircode:
                    raise ValidationError("Sports sessions require a location Eircode.")

        qs = SessionSlot.objects.filter(
            coach=self.coach,
            status__in=[self.Status.AVAILABLE, self.Status.BOOKED],
        ).exclude(pk=self.pk)

        overlap = qs.filter(
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        ).exists()

        if overlap:
            raise ValidationError("This slot overlaps with another slot you already created.")

    def __str__(self) -> str:
        return f"{self.coach.user.full_name()} | {self.skill.name} | {self.start_datetime:%Y-%m-%d %H:%M}"


class Booking(models.Model):
    """
    Booking created by a student for a session slot.

    Cancellation policy:
      - Students may cancel up to 24 hours before the session start.
      - After the 24-hour window the cancel button is hidden in the UI.
      - Coaches may cancel at any time from the dashboard.
      - Cancellation frees the slot back to AVAILABLE so another student
        can book it.

    Child bookings:
      - If child_profile is set, the child's name is shown on the booking
        instead of the parent's account name.
    """

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED  = "REJECTED",  "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    slot    = models.OneToOneField(SessionSlot, on_delete=models.PROTECT, related_name="booking")
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")

    # Optional: if booked on behalf of a child, store which child.
    # The parent's account remains the booking owner for GDPR purposes.
    child_profile = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="If set, the booking is on behalf of this child.",
    )

    status           = models.CharField(max_length=20, choices=Status.choices)
    meeting_link     = models.URLField(blank=True)
    student_location = models.CharField(max_length=255, blank=True)
    student_lat      = models.FloatField(null=True, blank=True)
    student_lng      = models.FloatField(null=True, blank=True)
    created_at       = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.student.full_name()} -> {self.slot}"

    def display_name(self) -> str:
        """
        Returns the child's name if this is a child booking,
        otherwise returns the parent/student's own name.
        """
        if self.child_profile:
            return self.child_profile.full_name()
        return self.student.full_name()

    def can_cancel(self) -> bool:
        """
        A student may cancel if the session hasn't started yet AND
        there is more than 24 hours remaining before the slot start.
        Coaches bypass this check and can cancel from the dashboard.
        """
        if self.status not in (self.Status.CONFIRMED, self.Status.PENDING):
            return False
        hours_until = (self.slot.start_datetime - timezone.now()).total_seconds() / 3600
        return hours_until > 24

    @staticmethod
    def create_booking(slot: SessionSlot, student: User, child_profile=None) -> "Booking":
        """
        Atomic booking to avoid double booking under concurrent requests.
        Online bookings: CONFIRMED instantly.
        In-person bookings: PENDING until coach accepts.
        """
        if student.role != User.Role.STUDENT:
            raise PermissionDenied("Only students/parents can make bookings.")

        if child_profile and child_profile.parent_id != student.id:
            raise PermissionDenied("That child profile does not belong to your account.")

        with transaction.atomic():
            locked = SessionSlot.objects.select_for_update().get(pk=slot.pk)

            if locked.status != SessionSlot.Status.AVAILABLE:
                raise ValidationError("This slot is no longer available.")

            booking_status = (
                Booking.Status.PENDING
                if locked.mode == SessionSlot.Mode.IN_PERSON
                else Booking.Status.CONFIRMED
            )

            locked.status = SessionSlot.Status.BOOKED
            locked.save(update_fields=["status"])

            return Booking.objects.create(
                slot=locked,
                student=student,
                child_profile=child_profile,
                status=booking_status,
            )


# -----------------------------------------------------------------
# REVIEW
# Students leave a 1-5 star review + optional comment after a
# CONFIRMED session that has already passed.
# One review per booking — enforced by the OneToOne field.
# The coach's average rating is computed via CoachProfile.average_rating().
# -----------------------------------------------------------------
class Review(models.Model):
    """
    Post-session review left by a student (or parent on behalf of a child).
    Linked one-to-one with a Booking so a student can only review once
    per session, preventing spam.
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="review",
    )
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 (poor) to 5 (excellent).",
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional written feedback.",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.booking.display_name()} → {self.coach} ({self.stars}★)"
