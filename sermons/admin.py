from django.contrib import admin

from .models import (
    Sermon,
    SermonSeries,
    SermonNote,
    SermonBookmark,
    SermonCategory,
    SermonCategoryTag,
)


@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'sermon_date', 'is_published', 'is_featured', 'view_count')
    list_filter = ('is_published', 'is_featured', 'sermon_type')
    search_fields = ('title', 'description', 'bible_references')
    date_hierarchy = 'sermon_date'


@admin.register(SermonSeries)
class SermonSeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'start_date', 'is_active')
    search_fields = ('title',)


admin.site.register(SermonNote)
admin.site.register(SermonBookmark)
admin.site.register(SermonCategory)
admin.site.register(SermonCategoryTag)
