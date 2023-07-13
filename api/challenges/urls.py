from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "api.challenges"
urlpatterns = [
    path ('list/', views.ChallengeListView.as_view (), name = 'challenge-list'),
    path ('category/list/', views.ChallengeCategoryListView.as_view (), name = 'challenge-category-list'),
    path ('detail/', views.ChallengeDetailView.as_view (), name = 'challenge-detail'),
    path ('obstacle-detail/', views.ObstacleDetailView.as_view (), name = 'obstacle-detail') ]
