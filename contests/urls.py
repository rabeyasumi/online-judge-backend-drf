from django.urls import path
from .views import ContestListView, ContestDetailView
from .views import (
    ContestListView,
    ContestDetailView,
    GlobalStandingListView,
    RatingChangeListView,
)
from submissions.views import ContestStandingsView

urlpatterns = [
    path('', ContestListView.as_view(), name='contest-list'),
    path('global-standings/', GlobalStandingListView.as_view(), name='global-standings'),
    path('rating-changes/', RatingChangeListView.as_view(), name='rating-changes'),
    path('<int:pk>/', ContestDetailView.as_view(), name='contest-detail'),
    path(
        '<int:contest_id>/standings/',
        ContestStandingsView.as_view(),
        name='contest-standings'
    ),
]