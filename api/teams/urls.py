from django.urls import path

from . import views

app_name = "api.team"
urlpatterns = [
    path ('detail/', views.TeamDetailView.as_view (), name='detail'),
    path ('create/', views.CreateTeamView.as_view (), name='create'),
    path ('invite/', views.InviteTeamView.as_view (), name='invite'),
    path ('leave/', views.LeaveTeamView.as_view (), name='leave-team'),
    path ('invitation/list/', views.InvitationListView.as_view (), name='list-invites'),
    path ('invitation/accept/', views.InvitationAcceptView.as_view (), name='accept-invite'),
    path ('invitation/decline/', views.InvitationDeclineView.as_view (), name='decline-invite'),
    path ('obstacle-activity-record/', views.TeamObstacleActivityRecordView.as_view(), name='obstacle-activity-record')
]
