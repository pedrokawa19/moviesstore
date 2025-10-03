from django.contrib import admin
from .models import Movie, Review, Report, MoviePetition, PetitionVote


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


class MoviePetitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'petitioner', 'created_at', 'is_active', 'admin_reviewed', 'vote_count')
    list_filter = ('is_active', 'admin_reviewed', 'created_at')
    search_fields = ('title', 'petitioner__username', 'description')
    actions = ['mark_reviewed', 'activate_petitions', 'deactivate_petitions']

    def vote_count(self, obj):
        return obj.get_vote_count()
    vote_count.short_description = 'Net Votes'

    def mark_reviewed(self, request, queryset):
        queryset.update(admin_reviewed=True)
    mark_reviewed.short_description = 'Mark selected petitions as reviewed'

    def activate_petitions(self, request, queryset):
        queryset.update(is_active=True)
    activate_petitions.short_description = 'Activate selected petitions'

    def deactivate_petitions(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_petitions.short_description = 'Deactivate selected petitions'


class PetitionVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'petition', 'voter', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('petition__title', 'voter__username')


admin.site.register(Movie, MovieAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(MoviePetition, MoviePetitionAdmin)
admin.site.register(PetitionVote, PetitionVoteAdmin)