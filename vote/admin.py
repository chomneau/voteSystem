from django.contrib import admin
from .models import Candidate, BallotToken, Vote


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
	list_display = ("name",)


@admin.register(BallotToken)
class BallotTokenAdmin(admin.ModelAdmin):
	list_display = ("user", "used", "created_at", "expires_at")
	readonly_fields = ("token",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
	list_display = ("candidate", "created_at")
