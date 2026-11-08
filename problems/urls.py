from django.urls import path
from .views import ProblemListView, ProblemDetailView

urlpatterns = [
    path('', ProblemListView.as_view(), name='problem-list'),
    path('<int:pk>/', ProblemDetailView.as_view(), name='problem-detail'),
]