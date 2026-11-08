from django.contrib import admin
from django.utils import timezone

from .models import Element, TestCase
from contests.models import Contest

from django import forms
from django.core.exceptions import ValidationError


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

class ElementAdminForm(forms.ModelForm):

    contest = forms.CharField(
        required=False,
        label="Contest Name",
        help_text="Enter exact contest name. Leave empty for standalone problem."
    )

    class Meta:
        model = Element
        fields = '__all__'

    def clean_contest(self):
        contest_name = self.cleaned_data.get('contest')

        if not contest_name or not contest_name.strip():
            return None

        try:
            return Contest.objects.get(cname__iexact=contest_name.strip())

        except Contest.DoesNotExist:
            raise ValidationError(
                f"Contest '{contest_name}' does not exist."
            )

        except Contest.MultipleObjectsReturned:
            raise ValidationError(
                "Multiple contests found with this name. Please use a unique contest name."
            )


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    form = ElementAdminForm
    inlines = [TestCaseInline]