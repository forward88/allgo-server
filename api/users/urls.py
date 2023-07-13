from django.urls import path

from . import views

app_name = "api.users"
urlpatterns = [
    path ('check-nickname-availability/', views.CheckNicknameAvailabilityView.as_view (), name='check-nickname-availability'),
    path ('claim-nickname/', views.ClaimNicknameView.as_view (), name='claim-nickname'),
    path ('detail/', views.UserProfileDetailView.as_view (), name='user-detail'),
    path ('challenge/list/', views.UserChallengeListView.as_view (), name='user-challenge-list'),
    path ('challenge/detail/', views.UserChallengeDetailView.as_view (), name='user-challenge-detail'),
    path ('obstacle/list/', views.UserObstacleListView.as_view (), name='user-obstacle-list'),
    path ('do-challenge-action/', views.UserChallengeActionView.as_view (), name='do-challenge-action'),
    path ('add-obstacle-activity/', views.AddObstacleActivityView.as_view (), name='add-obstacle-activity'),
    path ('obstacle-activity-record/', views.ObstacleActivityRecordView.as_view (), name='obstacle-activity-record'),
    path ('profile/options/', views.UserProfileOptionsView.as_view (), name='user-profile-options'),
    path ('profile/edit/', views.UserProfileEditView.as_view (), name='user-profile-edit'),
    path('delete-account/', views.UserDeleteAccountView.as_view(), name='user-delete-account')
]
