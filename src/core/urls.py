from django.urls import path
from . import views

urlpatterns = [
    # ── PUBLIC ───────────────────────────────────────────────────────────
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("find/", views.find_lessons, name="find_lessons"),

    # ── SIGNUP ───────────────────────────────────────────────────────────
    path("signup/", views.signup_choice, name="signup_choice"),
    path("signup/student/", views.signup_student, name="signup_student"),
    path("signup/coach/", views.signup_coach, name="signup_coach"),

    # Coach subscription selection — shown immediately after coach signup
    path("signup/coach/subscription/", views.signup_coach_subscription, name="signup_coach_subscription"),

    # ── STUDENT PROFILE AND BOOKINGS ─────────────────────────────────────
    path("profile/", views.my_profile, name="my_profile"),
    path("bookings/", views.student_upcoming, name="student_upcoming"),
    path("booking/<int:booking_id>/", views.booking_detail, name="booking_detail"),

    # ── STUDENT CANCELLATION ─────────────────────────────────────────────
    path("booking/<int:booking_id>/cancel/", views.student_cancel_booking, name="student_cancel_booking"),

    # ── Reviews ──────────────────────────────────────────────────────────
    # Student submits a review after a completed session
    path("booking/<int:booking_id>/review/", views.leave_review, name="leave_review"),

    # ── CHILD PROFILES ───────────────────────────────────────────────────
    path("children/", views.child_profile_list, name="child_profile_list"),
    path("children/add/", views.child_profile_add, name="child_profile_add"),
    path("children/<int:child_id>/delete/", views.child_profile_delete, name="child_profile_delete"),

    # ── MARKETPLACE ──────────────────────────────────────────────────────
    path("coach/<int:coach_id>/", views.coach_detail, name="coach_detail"),
    path("slot/<int:slot_id>/book/", views.book_slot, name="book_slot"),

    # ── Coach dashboard + coach actions ──────────────────────────────────
    path("coach/dashboard/", views.coach_dashboard, name="coach_dashboard"),
    path("coach/profile/edit/", views.coach_profile_edit, name="coach_profile_edit"),
    path("coach/slot/<int:slot_id>/cancel/", views.coach_cancel_slot, name="coach_cancel_slot"),
    path("coach/booking/<int:booking_id>/respond/", views.coach_respond_booking, name="coach_respond_booking"),
    path("coach/booking/<int:booking_id>/meeting-link/", views.coach_set_meeting_link, name="coach_set_meeting_link"),
]
