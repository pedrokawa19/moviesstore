from django.contrib import admin
from .models import Movie, Review, Report


class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'user', 'date', 'is_active', 'report_count')
    list_filter = ('is_active', 'date')
    search_fields = ('user__username', 'comment')
    actions = ['hide_reviews', 'reinstate_reviews']

    def report_count(self, obj):
        return obj.reports.count()

    def hide_reviews(self, request, queryset):
        queryset.update(is_active=False)

    def reinstate_reviews(self, request, queryset):
        queryset.update(is_active=True)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'reporter', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    search_fields = ('reporter__username', 'review__comment')


admin.site.register(Movie, MovieAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Report, ReportAdmin)