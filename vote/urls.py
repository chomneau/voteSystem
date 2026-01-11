from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="vote_landing"),
    path("qr_img/", views.display_qr, name="vote_qr_img"),
    path("start/", views.vote_start, name="vote_start"),
    path("waiting/<str:token>/", views.vote_waiting, name="vote_waiting"),
    path("result/", views.vote_result, name="vote_result"),
    path("<str:token>/", views.vote_view, name="vote"),
    path("api/voter_count/", views.voter_count_api, name="voter_count_api"),
    path("api/landing_stats/", views.landing_stats_api, name="landing_stats_api"),
    path("api/voting_status/", views.voting_status_api, name="voting_status_api"),
]
