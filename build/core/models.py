from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


# ── USER ──────────────────────────────────────────────────────────────────────
# We extend Django's built-in User model to add roles (Student or Coach)
# and extra profile fields like name, date of birth, and profile picture.

class User(AbstractUser):

    # Two possible roles for any user
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student/Parent"
        COACH   = "COACH",   "Coach/Teacher"

    class Gender(models.TextChoices):
        MALE       = "MALE",       "Male"
        FEMALE     = "FEMALE",     "Female"
        NON_BINARY = "NON_BINARY", "Non-binary"
        PREFER_NOT = "PREFER_NOT", "Prefer not to say"

    role    = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    forename        = models.CharField(max_length=80, blank=True)
    surname         = models.CharField(max_length=80, blank=True)
    dob             = models.DateField(null=True, blank=True)
    address         = models.CharField(max_length=255, blank=True)
    gender          = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    bio             = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def full_name(self):
        # Returns "First Last", or just the username if no name is set
        name = f"{self.forename} {self.surname}".strip()
        return name if name else self.username


# ── CATEGORY ─────────────────────────────────────────────────────────────────
# The three top-level lesson types: Grinds, Sports, Music

class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


# ── SKILL ─────────────────────────────────────────────────────────────────────
# A specific subject within a category, e.g. Maths (Grinds) or Guitar (Music)

class Skill(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="skills")
    name     = models.CharField(max_length=60)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.name} ({self.category.name})"


# ── AREA ──────────────────────────────────────────────────────────────────────
# Geographic areas used to filter in-person sessions (e.g. Dublin City)

class Area(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


# ── COACH SUBSCRIPTION ───────────────────────────────────────────────────────
# Tracks the plan a coach signed up on.
# Only FREE is active in this prototype; PRO is shown as "coming soon"
# to demonstrate the intended business model to evaluators.

class CoachSubscription(models.Model):

    class Tier(models.TextChoices):
        FREE = "FREE", "Free"
        PRO  = "PRO",  "Pro – €59.95/year"

    # One subscription per coach user
    coach_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    tier       = models.CharField(max_length=10, choices=Tier.choices, default=Tier.FREE)
    started_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.coach_user.username} — {self.get_tier_display()}"


# ── COACH PROFILE ─────────────────────────────────────────────────────────────
# Extra information stored for coach accounts only.
# Includes skills they teach, areas they cover, and their hourly rate.

class CoachProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name="coach_profile")
    category    = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="coaches")
    teaches     = models.ManyToManyField(Skill, blank=True, related_name="coaches")
    travel_areas = models.ManyToManyField(Area, blank=True, related_name="coaches")
    base_location_eircode = models.CharField(max_length=10, blank=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Admin sets this manually after Garda vetting — important for under-18 students
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.full_name()} - {self.category.name}"

    def average_rating(self):
        # Returns the average star rating, or None if no reviews yet
        reviews = self.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.stars for r in reviews) / reviews.count(), 1)

    def review_count(self):
        return self.reviews.count()


# ── CHILD PROFILE ─────────────────────────────────────────────────────────────
# A parent can create sub-profiles for their children.
# The child's name shows on bookings instead of the parent's.
# No separate login — GDPR Article 8 compliance (parental consent for minors).

class ChildProfile(models.Model):
    parent     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="child_profiles")
    forename   = models.CharField(max_length=80)
    surname    = models.CharField(max_length=80)
    dob        = models.DateField()
    year_group = models.CharField(max_length=40, blank=True)

    def full_name(self):
        return f"{self.forename} {self.surname}".strip()

    def __str__(self):
        return f"{self.full_name()} (child of {self.parent.username})"


# ── SESSION SLOT ──────────────────────────────────────────────────────────────
# A bookable time slot created by a coach.
# Slots can be Online or In Person, and track their status.

class SessionSlot(models.Model):

    class Mode(models.TextChoices):
        ONLINE    = "ONLINE",    "Online"
        IN_PERSON = "IN_PERSON", "In person"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED    = "BOOKED",    "Booked"
        CANCELLED = "CANCELLED", "Cancelled"

    coach          = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="slots")
    skill          = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="slots")
    mode           = models.CharField(max_length=20, choices=Mode.choices)
    area           = models.ForeignKey(Area, on_delete=models.PROTECT, null=True, blank=True, related_name="slots")
    venue_eircode  = models.CharField(max_length=10, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime   = models.DateTimeField()
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def clean(self):
        # Start must be before end
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start time must be before end time.")

        # Coach must teach this skill
        if self.coach_id and self.skill_id:
            if not self.coach.teaches.filter(pk=self.skill_id).exists():
                raise ValidationError("You can only create sessions for skills you teach.")

        # In-person slots must have an area
        if self.mode == self.Mode.IN_PERSON and self.area is None:
            raise ValidationError("In-person sessions must include an area for filtering.")

        # Sports must be in-person with an Eircode
        if self.skill_id and self.skill.category.name.lower() == "sports":
            if self.mode != self.Mode.IN_PERSON:
                raise ValidationError("Sports sessions must be in-person.")
            if not self.venue_eircode:
                raise ValidationError("Sports sessions require a location Eircode.")

        # No overlapping slots for the same coach
        overlap = SessionSlot.objects.filter(
            coach=self.coach,
            status__in=[self.Status.AVAILABLE, self.Status.BOOKED],
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        ).exclude(pk=self.pk).exists()

        if overlap:
            raise ValidationError("This slot overlaps with another slot you already created.")

    def __str__(self):
        return f"{self.coach.user.full_name()} | {self.skill.name} | {self.start_datetime:%Y-%m-%d %H:%M}"


# ── BOOKING ───────────────────────────────────────────────────────────────────
# A student books a session slot.
# Online bookings confirm instantly.
# In-person bookings go to the coach for approval (PENDING).
# Students can cancel up to 24 hours before the session.

class Booking(models.Model):

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED  = "REJECTED",  "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    slot             = models.OneToOneField(SessionSlot, on_delete=models.PROTECT, related_name="booking")
    student          = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")
    child_profile    = models.ForeignKey(ChildProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    status           = models.CharField(max_length=20, choices=Status.choices)
    meeting_link     = models.URLField(blank=True)
    student_location = models.CharField(max_length=255, blank=True)
    student_lat      = models.FloatField(null=True, blank=True)
    student_lng      = models.FloatField(null=True, blank=True)
    created_at       = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.full_name()} -> {self.slot}"

    def display_name(self):
        # Show child's name on booking if booked on behalf of a child
        if self.child_profile:
            return self.child_profile.full_name()
        return self.student.full_name()

    def can_cancel(self):
        # Students can only cancel if more than 24 hours remain before the session
        if self.status not in (self.Status.CONFIRMED, self.Status.PENDING):
            return False
        hours_until = (self.slot.start_datetime - timezone.now()).total_seconds() / 3600
        return hours_until > 24

    @staticmethod
    def create_booking(slot, student, child_profile=None):
        # Atomic booking prevents two students booking the same slot at the same time
        if student.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can make bookings.")

        if child_profile and child_profile.parent_id != student.id:
            raise PermissionDenied("That child profile does not belong to your account.")

        with transaction.atomic():
            # Lock the slot row so no other request can book it at the same time
            locked = SessionSlot.objects.select_for_update().get(pk=slot.pk)

            if locked.status != SessionSlot.Status.AVAILABLE:
                raise ValidationError("This slot is no longer available.")

            # Online = confirmed instantly, In-person = pending coach approval
            status = (
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
                status=status,
            )


# ── REVIEW ────────────────────────────────────────────────────────────────────
# Students leave a 1-5 star review after a confirmed session has ended.
# OneToOne on Booking means only one review per booking is allowed.

class Review(models.Model):
    booking    = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    coach      = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="reviews")
    stars      = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.booking.display_name()} → {self.coach} ({self.stars}★)"