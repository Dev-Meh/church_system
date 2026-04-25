from django.contrib import admin

from .models import ChurchUser, ChurchGroup, GroupMembership, GroupActivity


@admin.register(ChurchUser)
class ChurchUserAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "role", "is_active_member")
    list_filter = ("role", "is_active_member", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email", "phone_number")


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1


@admin.register(ChurchGroup)
class ChurchGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "group_type", "leader", "is_active")
    list_filter = ("group_type", "is_active")
    search_fields = ("name",)
    inlines = [GroupMembershipInline]


@admin.register(GroupActivity)
class GroupActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "activity_date", "created_by")
    list_filter = ("group", "activity_date")
    search_fields = ("title", "description")
