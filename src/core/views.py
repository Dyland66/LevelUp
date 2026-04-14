import datetime
import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    StudentSignUpForm, CoachSignUpForm, SubscriptionSelectForm,
    ProfileEditForm, CoachProfileEditForm, FindLessonsForm,
    SessionSlotForm, BookingMeetingLinkForm, BookingConfirmForm,
    ChildProfileForm, ReviewForm, RecurringAvailabilityForm,
)
from .models import (
    User, Category, Skill, Area, CoachProfile, CoachSubscription,
    ChildProfile, SessionSlot, Booking, Review,
)


# ── Helper: seed categories, skills and areas ─────────────────────────────────
# Ensures lookup data exists on first request.  Uses a module-level flag
# so the database is only checked once per server start, not every request.
# The same data is also created by:  python manage.py seed_coaches

_SEEDED = False


def _seed_data():
    global _SEEDED
    if _SEEDED:
        return

    grinds, _ = Category.objects.get_or_create(name="Grinds")
    sports, _ = Category.objects.get_or_create(name="Sports")
    music,  _ = Category.objects.get_or_create(name="Music")

    for s in [
        "Maths", "Irish", "English", "Biology", "Chemistry", "Physics",
        "Agricultural Science", "Accounting", "Business", "Economics",
        "Geography", "History", "Art", "Music", "Home Economics",
        "French", "German", "Spanish", "Italian", "Japanese", "Mandarin Chinese",
        "Latin", "Classical Studies", "Religious Education", "Physical Education",
        "Computer Science", "Design and Communication Graphics",
        "Construction Studies", "Engineering", "Technology",
        "Applied Maths", "Politics and Society",
    ]:
        Skill.objects.get_or_create(category=grinds, name=s)

    for s in ["Padel", "Gym PT", "Football Coaching", "Golf"]:
        Skill.objects.get_or_create(category=sports, name=s)

    for s in ["Guitar", "Piano", "Violin"]:
        Skill.objects.get_or_create(category=music, name=s)

    for a in ["Dublin City", "Dublin 2", "Tallaght", "Swords", "Cork City", "Galway City"]:
        Area.objects.get_or_create(name=a)

    _SEEDED = True


# ── Helper: calendar event colour and label ───────────────────────────────────
# Both the public coach page and the coach dashboard need to colour-code
# calendar slots the same way, so this avoids duplicating that logic.

def _slot_label_and_colour(slot, category_name, booked_name=None):
    area_str = slot.area.name if slot.area else ""

    # Booked slots show grey with the student's name
    if booked_name:
        return f"{slot.skill.name} — ✓ {booked_name}", "#6b7280"

    # In-person slots are amber
    if slot.mode == SessionSlot.Mode.IN_PERSON:
        label = f"{slot.skill.name} — 📍 {area_str}" if area_str else f"{slot.skill.name} — 📍 In person"
        return label, "#b45309"

    # Online slots — colour depends on category
    colours = {"Grinds": "#1a6b3c", "Music": "#5b3fd4"}
    return f"{slot.skill.name} — 💻 Online", colours.get(category_name, "#0369a1")


# ── Public pages ──────────────────────────────────────────────────────────────

def home(request):
    _seed_data()
    return render(request, "core/home.html", {"categories": Category.objects.all()})


def about(request):
    return render(request, "core/about.html")


def signup_choice(request):
    return render(request, "core/signup_choice.html")


def signup_student(request):
    # Create a student account, set the role, and log them in straight away
    form = StudentSignUpForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.role = User.Role.STUDENT
        user.save()
        login(request, user)
        return redirect("home")
    return render(request, "core/signup_student.html", {"form": form})


def signup_coach(request):
    # Create a coach account with a linked CoachProfile, then redirect to subscription selection
    _seed_data()
    form = CoachSignUpForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.role = User.Role.COACH
        user.save()
        CoachProfile.objects.create(user=user, category=form.cleaned_data["category"])
        login(request, user)
        return redirect("signup_coach_subscription")
    return render(request, "core/signup_coach.html", {"form": form})


def signup_coach_subscription(request):
    # Redirect away if the user is not a coach or already has a subscription
    if not request.user.is_authenticated or request.user.role != User.Role.COACH:
        return redirect("signup_coach")
    if hasattr(request.user, "subscription"):
        return redirect("coach_profile_edit")
    form = SubscriptionSelectForm(request.POST or None)
    if form.is_valid():
        CoachSubscription.objects.create(coach_user=request.user, tier=form.cleaned_data["tier"])
        return redirect("coach_profile_edit")
    return render(request, "core/signup_coach_subscription.html", {"form": form})


# ── Student pages ─────────────────────────────────────────────────────────────

@login_required
def my_profile(request):
    # Let any logged-in user edit their name, email, and profile photo
    form = ProfileEditForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        # Coaches go back to their dashboard; students stay on this page
        return redirect("coach_dashboard" if request.user.role == User.Role.COACH else "my_profile")
    return render(request, "core/my_profile.html", {"form": form})


@login_required
def child_profile_list(request):
    # Show all child profiles belonging to this parent (students only)
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    return render(request, "core/child_profile_list.html", {"children": request.user.child_profiles.all()})


@login_required
def child_profile_add(request):
    # Let a parent add a child profile so they can book lessons on their behalf
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    form = ChildProfileForm(request.POST or None)
    if form.is_valid():
        child = form.save(commit=False)
        child.parent = request.user
        child.save()
        messages.success(request, f"Profile for {child.full_name()} added.")
        return redirect("child_profile_list")
    return render(request, "core/child_profile_form.html", {"form": form, "action": "Add"})


@login_required
def child_profile_delete(request, child_id):
    # Remove a child profile — only allowed via POST to prevent accidental deletion
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    child = get_object_or_404(ChildProfile, pk=child_id, parent=request.user)
    if request.method == "POST":
        child.delete()
        messages.success(request, "Child profile removed.")
    return redirect("child_profile_list")


def find_lessons(request):
    # Main search page — students filter available slots by category, skill, mode, area or name
    _seed_data()
    form = FindLessonsForm(request.GET or None)

    # Only show results after the user has submitted the search form
    searched = bool(request.GET)
    coach_cards = {}

    if searched and form.is_valid():
        # Start with all available slots
        qs = SessionSlot.objects.filter(status=SessionSlot.Status.AVAILABLE).select_related("coach", "coach__user", "skill", "skill__category", "area")

        # Apply whichever filters the user selected
        if form.cleaned_data.get("category"):
            qs = qs.filter(skill__category=form.cleaned_data["category"])
        if form.cleaned_data.get("skill"):
            qs = qs.filter(skill=form.cleaned_data["skill"])
        if form.cleaned_data.get("mode"):
            qs = qs.filter(mode=form.cleaned_data["mode"])
        if form.cleaned_data.get("area"):
            qs = qs.filter(area=form.cleaned_data["area"])
        if form.cleaned_data.get("coach_name"):
            # Name search: if multiple words, match first against forename and
            # last against surname.  Single word uses OR to check both fields.
            name = form.cleaned_data["coach_name"].strip()
            parts = name.split()
            if len(parts) > 1:
                qs = qs.filter(
                    coach__user__forename__icontains=parts[0],
                    coach__user__surname__icontains=parts[-1],
                )
            else:
                qs = qs.filter(
                    Q(coach__user__forename__icontains=name)
                    | Q(coach__user__surname__icontains=name)
                )

        # Group results by coach — each coach card shows their earliest available slot
        for slot in qs.order_by("start_datetime"):
            if slot.coach_id not in coach_cards:
                coach_cards[slot.coach_id] = {
                    "coach":        slot.coach,
                    "next_slot":    slot,
                    "avg_rating":   slot.coach.average_rating(),
                    "review_count": slot.coach.review_count(),
                }

    return render(request, "core/find_lessons.html", {
        "form":        form,
        "coach_cards": list(coach_cards.values()),
        "searched":    searched,
    })


def coach_detail(request, coach_id):
    # Public coach profile page — shows bio, calendar of available slots, and reviews
    coach = get_object_or_404(CoachProfile.objects.select_related("user", "category"), pk=coach_id)

    # Optional mode filter passed from the find lessons page
    mode_filter = request.GET.get("mode", "")

    slots = coach.slots.filter(status=SessionSlot.Status.AVAILABLE).select_related("skill", "area").order_by("start_datetime")
    if mode_filter in (SessionSlot.Mode.ONLINE, SessionSlot.Mode.IN_PERSON):
        slots = slots.filter(mode=mode_filter)

    reviews = coach.reviews.select_related("booking__student").order_by("-created_at")

    # Build the list of events for FullCalendar
    calendar_events = []
    for slot in slots:
        label, bg = _slot_label_and_colour(slot, coach.category.name)
        area_str = slot.area.name if slot.area else ""

        calendar_events.append({
            "id":              slot.id,
            "title":           label,
            "start":           slot.start_datetime.isoformat(),
            "end":             slot.end_datetime.isoformat(),
            "url":             f"/slot/{slot.id}/book/",
            "backgroundColor": bg,
            "borderColor":     "transparent",
            "textColor":       "#ffffff",
            "extendedProps": {
                "mode":   slot.get_mode_display(),
                "area":   f"{area_str} ({slot.venue_eircode})" if slot.venue_eircode else area_str,
                "skill":  slot.skill.name,
                "slotId": slot.id,
            },
        })

    return render(request, "core/coach_detail.html", {
        "coach":                coach,
        "slots":                slots,
        "reviews":              reviews,
        "avg_rating":           coach.average_rating(),
        "review_count":         coach.review_count(),
        "mode_filter":          mode_filter,
        "calendar_events_json": json.dumps(calendar_events),
    })


@login_required
def book_slot(request, slot_id):
    # Book an available slot — students only. Uses create_booking() which
    # prevents double-booking with a database lock.
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    slot = get_object_or_404(SessionSlot.objects.select_related("coach", "coach__user", "skill", "area"), pk=slot_id)

    form = BookingConfirmForm(request.POST or None)
    form.fields["child_profile"].queryset = ChildProfile.objects.filter(parent=request.user)

    if form.is_valid():
        try:
            booking = Booking.create_booking(
                slot=slot,
                student=request.user,
                child_profile=form.cleaned_data.get("child_profile"),
            )
            # Save student address and coordinates for in-person grinds/music
            if slot.mode == SessionSlot.Mode.IN_PERSON and slot.skill.category.name.lower() != "sports":
                booking.student_location = form.cleaned_data.get("student_location", "")
                booking.student_lat      = form.cleaned_data.get("student_lat") or None
                booking.student_lng      = form.cleaned_data.get("student_lng") or None
                booking.save(update_fields=["student_location", "student_lat", "student_lng"])
            return redirect("booking_detail", booking_id=booking.id)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect("coach_detail", coach_id=slot.coach_id)

    return render(request, "core/booking_confirm.html", {"slot": slot, "form": form})


@login_required
def student_upcoming(request):
    # List all of this student's bookings (upcoming and past) in date order
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    bookings = Booking.objects.filter(student=request.user).select_related(
        "slot", "slot__coach", "slot__coach__user", "slot__skill", "slot__area", "child_profile"
    ).order_by("slot__start_datetime")
    return render(request, "core/student_upcoming.html", {"bookings": bookings, "now": timezone.now()})


@login_required
def student_cancel_booking(request, booking_id):
    # Cancel a booking if >24 hours remain, and free the slot for other students
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    booking = get_object_or_404(Booking, pk=booking_id, student=request.user)
    if not booking.can_cancel():
        messages.error(request, "Cannot cancel — session starts in less than 24 hours.")
        return redirect("student_upcoming")
    if request.method == "POST":
        # Cancel the booking and free the slot back up
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        booking.slot.status = SessionSlot.Status.AVAILABLE
        booking.slot.save(update_fields=["status"])
        messages.success(request, "Booking cancelled.")
        return redirect("student_upcoming")
    return render(request, "core/booking_cancel_confirm.html", {"booking": booking})


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("slot", "slot__coach", "slot__coach__user", "slot__skill", "slot__area", "child_profile"),
        pk=booking_id,
    )
    # Only the student or the coach involved can view this booking
    if request.user.role == User.Role.STUDENT and booking.student_id != request.user.id:
        raise PermissionDenied
    if request.user.role == User.Role.COACH and booking.slot.coach.user_id != request.user.id:
        raise PermissionDenied

    # Show the review button only if the session has ended and no review exists yet
    can_review = (
        request.user.role == User.Role.STUDENT
        and booking.status == Booking.Status.CONFIRMED
        and booking.slot.end_datetime < timezone.now()
        and not hasattr(booking, "review")
    )
    return render(request, "core/booking_detail.html", {"booking": booking, "can_review": can_review, "now": timezone.now()})


@login_required
def leave_review(request, booking_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    booking = get_object_or_404(Booking.objects.select_related("slot", "slot__coach"), pk=booking_id, student=request.user)

    # Only allow reviews on completed confirmed sessions with no review yet
    if booking.status != Booking.Status.CONFIRMED or booking.slot.end_datetime >= timezone.now() or hasattr(booking, "review"):
        messages.error(request, "Review not available for this booking.")
        return redirect("booking_detail", booking_id=booking_id)

    form = ReviewForm(request.POST or None)
    if form.is_valid():
        review = form.save(commit=False)
        review.booking = booking
        review.coach   = booking.slot.coach
        review.save()
        messages.success(request, "Review submitted!")
        return redirect("booking_detail", booking_id=booking_id)
    return render(request, "core/leave_review.html", {"booking": booking, "form": form})


# ── Coach pages ───────────────────────────────────────────────────────────────

@login_required
def coach_profile_edit(request):
    # Let a coach update their public profile (bio, skills, verified status)
    if request.user.role != User.Role.COACH:
        raise PermissionDenied
    coach = get_object_or_404(CoachProfile, user=request.user)
    form = CoachProfileEditForm(request.POST or None, instance=coach, category=coach.category)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("coach_dashboard")
    return render(request, "core/coach_profile_edit.html", {"coach": coach, "form": form})


@login_required
def coach_dashboard(request):
    # Main hub for coaches — create slots, manage bookings, view schedule calendar
    if request.user.role != User.Role.COACH:
        raise PermissionDenied
    coach = get_object_or_404(CoachProfile, user=request.user)

    slot_form      = SessionSlotForm(coach_profile=coach)
    recurring_form = RecurringAvailabilityForm(coach_profile=coach)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_slot": ### Single session creation
            slot_form = SessionSlotForm(request.POST, coach_profile=coach)
            if slot_form.is_valid():
                slot_form.save()
                messages.success(request, "Slot created.")
                return redirect("coach_dashboard")
            messages.error(request, "Fix the errors below.")

        elif action == "create_recurring": ### Recurring session creation
            recurring_form = RecurringAvailabilityForm(request.POST, coach_profile=coach)
            if recurring_form.is_valid():
                d          = recurring_form.cleaned_data
                target_dow = int(d["day_of_week"])
                duration   = datetime.timedelta(minutes=int(d["slot_duration_minutes"]))
                today      = datetime.date.today()
                # Work out days until the next occurrence of the chosen weekday
                days_ahead = (target_dow - today.weekday()) % 7 or 7
                first_date = today + datetime.timedelta(days=days_ahead)
                created    = 0

                # Generate one slot per week for the requested number of weeks
                for week in range(int(d["weeks_ahead"])):
                    slot_date = first_date + datetime.timedelta(weeks=week)
                    start_dt  = timezone.make_aware(datetime.datetime.combine(slot_date, d["start_time"]))
                    slot = SessionSlot(
                        coach=coach, skill=d["skill"], mode=d["mode"],
                        area=d["area"], venue_eircode=d["venue_eircode"],
                        start_datetime=start_dt, end_datetime=start_dt + duration,
                    )
                    try:
                        slot.full_clean()
                        slot.save()
                        created += 1
                    except ValidationError:
                        pass  # skip slots that fail validation (e.g. overlaps)

                if created:
                    messages.success(request, f"{created} slot(s) created.")
                else:
                    messages.error(request, "No slots created — check for overlaps.")
                return redirect("coach_dashboard")
            messages.error(request, "Fix the errors below.")

    # Build calendar events for the coach's schedule view
    all_slots = SessionSlot.objects.filter(
        coach=coach,
        status__in=[SessionSlot.Status.AVAILABLE, SessionSlot.Status.BOOKED]
    ).select_related("skill", "area").order_by("start_datetime")

    dashboard_calendar_events = []
    for slot in all_slots:
        # For booked slots, pass the student's name; available slots get None
        booked_name = None
        if slot.status != SessionSlot.Status.AVAILABLE:
            try:
                booked_name = slot.booking.display_name()
            except (AttributeError, Booking.DoesNotExist):
                booked_name = "Booked"

        label, bg = _slot_label_and_colour(slot, coach.category.name, booked_name)
        area_str = slot.area.name if slot.area else ""

        dashboard_calendar_events.append({
            "id":              slot.id,
            "title":           label,
            "start":           slot.start_datetime.isoformat(),
            "end":             slot.end_datetime.isoformat(),
            "backgroundColor": bg,
            "borderColor":     "transparent",
            "textColor":       "#ffffff",
            "extendedProps":   {"status": slot.status, "mode": slot.get_mode_display(), "area": area_str, "skill": slot.skill.name},
        })

    return render(request, "core/coach_dashboard.html", {
        "coach":          coach,
        "slot_form":      slot_form,
        "recurring_form": recurring_form,
        "pending_bookings":  Booking.objects.filter(slot__coach=coach, status=Booking.Status.PENDING).select_related("student", "slot", "slot__skill", "slot__area", "child_profile"),
        "upcoming_bookings": Booking.objects.filter(slot__coach=coach, status=Booking.Status.CONFIRMED).select_related("student", "slot", "slot__skill", "slot__area", "child_profile"),
        "available_slots":   SessionSlot.objects.filter(coach=coach, status=SessionSlot.Status.AVAILABLE).select_related("skill", "area").order_by("start_datetime"),
        "avg_rating":        coach.average_rating(),
        "review_count":      coach.review_count(),
        "recent_reviews":    coach.reviews.order_by("-created_at")[:5],
        "dashboard_calendar_events_json": json.dumps(dashboard_calendar_events),
    })


@login_required
def coach_cancel_slot(request, slot_id):
    # Remove an available slot from the coach's calendar (POST only)
    if request.user.role != User.Role.COACH:
        raise PermissionDenied
    coach = get_object_or_404(CoachProfile, user=request.user)
    slot  = get_object_or_404(SessionSlot, pk=slot_id, coach=coach)
    if request.method == "POST" and slot.status == SessionSlot.Status.AVAILABLE:
        slot.status = SessionSlot.Status.CANCELLED
        slot.save(update_fields=["status"])
        messages.success(request, "Slot cancelled.")
    return redirect("coach_dashboard")


@login_required
def coach_respond_booking(request, booking_id):
    # Accept or reject a pending in-person booking request
    if request.user.role != User.Role.COACH:
        raise PermissionDenied
    booking = get_object_or_404(Booking.objects.select_related("slot", "slot__coach", "student"), pk=booking_id)
    if booking.slot.coach.user_id != request.user.id:
        raise PermissionDenied
    if request.method == "POST" and booking.status == Booking.Status.PENDING:
        if request.POST.get("decision") == "accept":
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])
            messages.success(request, "Booking accepted.")
        elif request.POST.get("decision") == "reject":
            booking.status = Booking.Status.REJECTED
            booking.save(update_fields=["status"])
            # Free the slot back up so another student can book it
            booking.slot.status = SessionSlot.Status.AVAILABLE
            booking.slot.save(update_fields=["status"])
            messages.success(request, "Booking rejected.")
    return redirect("coach_dashboard")


@login_required
def coach_set_meeting_link(request, booking_id):
    # Let a coach add or update the Zoom/Teams link for an online booking
    if request.user.role != User.Role.COACH:
        raise PermissionDenied
    booking = get_object_or_404(Booking.objects.select_related("slot", "slot__coach"), pk=booking_id)
    if booking.slot.coach.user_id != request.user.id:
        raise PermissionDenied
    form = BookingMeetingLinkForm(request.POST or None, instance=booking)
    if form.is_valid():
        form.save()
        messages.success(request, "Meeting link updated.")
        return redirect("coach_dashboard")
    return render(request, "core/coach_meeting_link.html", {"booking": booking, "form": form})