from django.contrib import admin
from django.urls import include, path

from landing import views as landing_views

urlpatterns = [
    path ('', landing_views.landing),
    path ('admin/', admin.site.urls),
    path ('landing/', include ('landing.urls', namespace = 'landing')),
    path ('api/doc/', include ('api.doc.urls', namespace = 'api.doc')),
    path ('api/auth/', include ('api.rest_auth.urls', namespace = 'api.rest_auth')),
    path ('api/user/', include ('api.users.urls', namespace = 'api.users')),
    path ('api/team/', include ('api.teams.urls', namespace = 'api.teams')),
    path ('api/challenge/', include ('api.challenges.urls', namespace = 'api.challenges')),
    path ('api/scoring/', include ('api.scoring.urls', namespace = 'api.scoring')) ]
