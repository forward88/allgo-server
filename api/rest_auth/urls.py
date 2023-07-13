from django.urls import path

from . import views

app_name = "api.rest_auth"
urlpatterns = [
    path ('request-phone-verification/', views.RequestPhoneVerificationView.as_view (), name='request-phone-verification'),
    path ('sign-in/', views.SignInView.as_view (), name='sign-in'),
    path ('refresh-tokens/', views.RefreshTokensView.as_view (), name='refresh-tokens') ]
