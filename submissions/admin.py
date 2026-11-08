from django.contrib import admin
from .models import Submission, Standings
from accounts.models import Student 

from .views import update_contest_standing


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'student',
        'element',
        'contest',
        'verdict',
        'submitted_at',
    )

    list_filter = ('student', 'verdict', 'contest', 'language')
    search_fields = ('student__handle', 'element__name')

    actions = ['recalculate_standings']     # for the admin add data

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == 'student':
            kwargs['queryset'] = Student.objects.all()

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)   # saves the Submission
        update_contest_standing(obj)                       # then updates Standings

    @admin.action(description='Recalculate standings for selected submissions')
    def recalculate_standings(self, request, queryset):
        for sub in queryset.select_related('contest', 'student'):
            update_contest_standing(sub)
        self.message_user(request, 'Standings recalculated.')


admin.site.register(Standings)
