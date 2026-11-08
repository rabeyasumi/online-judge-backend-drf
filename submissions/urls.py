from django.urls import path
from .views import (
    MySubmissionListView,
    LanguageListView,
    SubmitCodeView,
    AllSubmissionListView
)

urlpatterns = [
    path('all/', AllSubmissionListView.as_view(), name='all-submissions'),
    path('my/', MySubmissionListView.as_view(), name='my-submissions'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('', SubmitCodeView.as_view(), name='submit-code'),
]