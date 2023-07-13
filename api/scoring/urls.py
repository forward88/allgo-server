from django.urls import path

from . import views

app_name = 'api.scoring'
urlpatterns = [
    path ('achievement/list/', views.AchievementListView.as_view (), name='achievement-list') ]
