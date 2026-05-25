from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'

    def ready(self):
        from django.db.models.signals import post_migrate, post_save

        def create_default_groups(sender, **kwargs):
            if sender.name != 'members':
                return
            from .group_services import (
                ensure_default_church_groups,
                sync_all_auto_group_memberships,
            )

            ensure_default_church_groups()
            sync_all_auto_group_memberships()

        post_migrate.connect(create_default_groups, dispatch_uid='members_default_groups')

        from .models import ChurchUser

        def sync_groups_on_member_save(sender, instance, **kwargs):
            from .group_services import sync_member_auto_groups

            sync_member_auto_groups(instance)

        post_save.connect(
            sync_groups_on_member_save,
            sender=ChurchUser,
            dispatch_uid='members_sync_auto_groups',
        )
