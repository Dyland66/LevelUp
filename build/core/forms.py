from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Category, Skill, Area, CoachProfile, ChildProfile, SessionSlot, Booking, Review


# ── STUDENT SIGN-UP ───────────────────────────────────────────────────────────

class StudentSignUpForm(UserCreationForm):
    dob = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = ("username", "email", "forename", "surname", "dob", "address", "gender")


# ── COACH SIGN-UP ─────────────────────────────────────────────────────────────

class CoachSignUpForm(UserCreationForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    dob      = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = ("username", "email", "forename", "surname", "dob")


# ── SUBSCRIPTION SELECTION ────────────────────────────────────────────────────
# Only FREE is active; PRO is shown as coming soon for demo purposes

class SubscriptionSelectForm(forms.Form):
    tier = forms.ChoiceField(
        choices=[("FREE", "Free — €0/year  ✓ All core features included")],
        widget=forms.RadioSelect,
        initial="FREE",
        label="Choose your plan",
    )


# ── PROFILE EDIT (STUDENT & COACH) ────────────────────────────────────────────

class ProfileEditForm(forms.ModelForm):
    dob = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model  = User
        fields = ("forename", "surname", "email", "dob", "address", "gender", "bio", "profile_picture")


# ── COACH PROFILE EDIT ────────────────────────────────────────────────────────
# Lets the coach update their skills, areas, and hourly rate

class CoachProfileEditForm(forms.ModelForm):
    teaches = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    travel_areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model  = CoachProfile
        fields = ("hourly_rate", "base_location_eircode", "teaches", "travel_areas")

    def __init__(self, *args, **kwargs):
        # Filter skills to only the coach's category
        category = kwargs.pop("category", None)
        super().__init__(*args, **kwargs)
        if category:
            self.fields["teaches"].queryset = Skill.objects.filter(category=category)


# ── FIND LESSONS FILTER ───────────────────────────────────────────────────────

class FindLessonsForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="Any category")
    skill    = forms.ModelChoiceField(queryset=Skill.objects.select_related("category").all(), required=False, empty_label="Any subject / skill", label="Subject / Skill")
    mode     = forms.ChoiceField(choices=[("", "Any mode"), ("ONLINE", "Online"), ("IN_PERSON", "In person")], required=False)
    area     = forms.ModelChoiceField(queryset=Area.objects.all(), required=False, empty_label="Any area")


# ── SESSION SLOT CREATION (COACH DASHBOARD) ───────────────────────────────────

class SessionSlotForm(forms.ModelForm):
    class Meta:
        model   = SessionSlot
        fields  = ("skill", "mode", "area", "venue_eircode", "start_datetime", "end_datetime")
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime":   forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        coach_profile = kwargs.pop("coach_profile")
        super().__init__(*args, **kwargs)
        self.instance.coach = coach_profile
        # Only show skills the coach actually teaches
        self.fields["skill"].queryset = coach_profile.teaches.all()


# ── MEETING LINK (COACH – ONLINE SESSIONS) ────────────────────────────────────

class BookingMeetingLinkForm(forms.ModelForm):
    class Meta:
        model  = Booking
        fields = ("meeting_link",)


# ── BOOKING CONFIRMATION ──────────────────────────────────────────────────────
# Includes hidden lat/lng fields filled by Google Maps autocomplete

class BookingConfirmForm(forms.Form):
    child_profile = forms.ModelChoiceField(
        queryset=ChildProfile.objects.none(),
        required=False,
        empty_label="Booking for myself",
        label="Who is this booking for?",
    )
    student_location = forms.CharField(
        required=False,
        label="Your address",
        widget=forms.TextInput(attrs={"placeholder": "Start typing your address..."}),
    )
    student_lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    student_lng = forms.FloatField(required=False, widget=forms.HiddenInput())


# ── CHILD PROFILE ─────────────────────────────────────────────────────────────

class ChildProfileForm(forms.ModelForm):
    dob = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model  = ChildProfile
        fields = ("forename", "surname", "dob", "year_group")


# ── REVIEW ────────────────────────────────────────────────────────────────────

class ReviewForm(forms.ModelForm):
    # Show stars as radio buttons (1–5)
    stars = forms.ChoiceField(
        choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Your rating",
    )

    class Meta:
        model   = Review
        fields  = ("stars", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Optional — share your experience."})}
        labels  = {"comment": "Written feedback (optional)"}

    def clean_stars(self):
        # ChoiceField returns a string so convert to int
        return int(self.cleaned_data["stars"])


# ── RECURRING AVAILABILITY (COACH DASHBOARD) ──────────────────────────────────
# Coach picks a day/time pattern and slots are auto-generated for multiple weeks

class RecurringAvailabilityForm(forms.Form):
    DAY_CHOICES = [(0,"Monday"),(1,"Tuesday"),(2,"Wednesday"),(3,"Thursday"),(4,"Friday"),(5,"Saturday"),(6,"Sunday")]
    DURATION_CHOICES = [(30,"30 minutes"),(60,"1 hour"),(90,"1.5 hours"),(120,"2 hours")]
    WEEKS_CHOICES = [(i, f"{i} week{'s' if i > 1 else ''}") for i in range(1, 9)]

    skill                = forms.ModelChoiceField(queryset=Skill.objects.none(), label="Subject / Skill")
    mode                 = forms.ChoiceField(choices=SessionSlot.Mode.choices)
    area                 = forms.ModelChoiceField(queryset=Area.objects.all(), required=False, empty_label="— Select area (in-person only) —")
    venue_eircode        = forms.CharField(required=False, label="Venue Eircode (sports only)", widget=forms.TextInput(attrs={"placeholder": "e.g. D02 XY45"}))
    day_of_week          = forms.ChoiceField(choices=DAY_CHOICES, label="Day of week")
    start_time           = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}), label="Start time")
    slot_duration_minutes = forms.ChoiceField(choices=DURATION_CHOICES, label="Slot duration")
    weeks_ahead          = forms.ChoiceField(choices=WEEKS_CHOICES, label="Generate for how many weeks?")

    def __init__(self, *args, **kwargs):
        coach_profile = kwargs.pop("coach_profile")
        super().__init__(*args, **kwargs)
        # Only show skills the coach teaches
        self.fields["skill"].queryset = coach_profile.teaches.all()