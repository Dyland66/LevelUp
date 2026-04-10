from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    User,
    Category,
    Skill,
    Area,
    CoachSubscription,
    CoachProfile,
    ChildProfile,
    SessionSlot,
    Booking,
    Review,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "LevelUp Profile",
            {
                "fields": (
                    "role",
                    "forename",
                    "surname",
                    "dob",
                    "address",
                    "gender",
                    "bio",
                    "profile_picture",
                )
            },
        ),
    )
    list_display  = ("username", "email", "role", "forename", "surname", "is_staff")
    list_filter   = ("role", "is_staff", "is_superuser")
    search_fields = ("username", "email", "forename", "surname")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name",)
    search_fields = ("name",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ("name", "category")
    list_filter   = ("category",)
    search_fields = ("name",)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display  = ("name",)
    search_fields = ("name",)


@admin.register(CoachSubscription)
class CoachSubscriptionAdmin(admin.ModelAdmin):
    list_display  = ("coach_user", "tier", "started_at")
    list_filter   = ("tier",)
    search_fields = ("coach_user__username", "coach_user__email")


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display      = ("user", "category", "hourly_rate", "is_verified", "base_location_eircode")
    list_filter       = ("category", "is_verified")
    search_fields     = ("user__username", "user__email", "user__forename", "user__surname")
    filter_horizontal = ("teaches", "travel_areas")


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display  = ("full_name_display", "parent", "dob", "year_group")
    search_fields = ("forename", "surname", "parent__username", "parent__email")
    list_filter   = ("year_group",)

    def full_name_display(self, obj):
        return obj.full_name()
    full_name_display.short_description = "Child Name"


@admin.register(SessionSlot)
class SessionSlotAdmin(admin.ModelAdmin):
    list_display  = ("coach", "skill", "mode", "area", "start_datetime", "end_datetime", "status")
    list_filter   = ("mode", "status", "skill__category", "area")
    search_fields = ("coach__user__username", "skill__name", "venue_eircode")
    ordering      = ("-start_datetime",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ("slot", "student", "child_profile", "status", "created_at")
    list_filter   = ("status", "slot__mode", "slot__skill__category")
    search_fields = ("student__username", "student__email", "slot__skill__name")
    ordering      = ("-created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display    = ("booking", "coach", "stars", "created_at")
    list_filter     = ("stars", "coach__category")
    search_fields   = ("booking__student__username", "coach__user__username", "comment")
    ordering        = ("-created_at",)
    readonly_fields = ("booking", "coach", "stars", "comment", "created_at")