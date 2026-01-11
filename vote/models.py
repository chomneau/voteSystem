from django.db import models
from django.contrib.auth import get_user_model
import secrets
import random
from django.utils import timezone


User = get_user_model()

def generate_token():
	# Generate a unique 6-digit code as a string
	# Import inside function to avoid circular import, but use string reference
	from django.apps import apps
	while True:
		code = f"{random.randint(0, 999999):06d}"
		try:
			BallotToken = apps.get_model('vote', 'BallotToken')
			if not BallotToken.objects.filter(token=code).exists():
				return code
		except LookupError:
			# Model not yet registered (during initial migration)
			return code

class Candidate(models.Model):
	name = models.CharField(max_length=200)
	bio = models.TextField(blank=True)

	def __str__(self):
		return self.name

class DeviceFingerprint(models.Model):
	"""Store device fingerprints to detect duplicate voters across sessions"""
	fingerprint_hash = models.CharField(max_length=256, unique=True, db_index=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)
	has_voted = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Device {self.fingerprint_hash[:16]}... ({'voted' if self.has_voted else 'not voted'})"

class BallotToken(models.Model):
	token = models.CharField(max_length=128, unique=True, default=generate_token)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # allow anonymous
	device_fingerprint = models.ForeignKey(DeviceFingerprint, on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	used = models.BooleanField(default=False)
	used_at = models.DateTimeField(null=True, blank=True)
	expires_at = models.DateTimeField(null=True, blank=True)

	def is_valid(self):
		if self.used:
			return False
		if self.expires_at and timezone.now() > self.expires_at:
			return False
		return True

	def __str__(self):
		return f"Token for {self.user} ({'used' if self.used else 'unused'})"

class Vote(models.Model):
	candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True)
	token_value = models.CharField(max_length=128, null=True, blank=True)

	def __str__(self):
		return f"Vote for {self.candidate} at {self.created_at}"


# Place VotingStatus model after all imports and other models

class VotingStatus(models.Model):
	is_open = models.BooleanField(default=False)
	updated_at = models.DateTimeField(auto_now=True)

	@classmethod
	def get_status(cls):
		obj, _ = cls.objects.get_or_create(pk=1)
		return obj

User = get_user_model()


def generate_token():
	# Generate a unique 6-digit code as a string
	from .models import BallotToken
	while True:
		code = f"{random.randint(0, 999999):06d}"
		if not BallotToken.objects.filter(token=code).exists():
			return code


class Candidate(models.Model):
	name = models.CharField(max_length=200)
	bio = models.TextField(blank=True)

	def __str__(self):
		return self.name



class BallotToken(models.Model):
	token = models.CharField(max_length=128, unique=True, default=generate_token)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # allow anonymous
	created_at = models.DateTimeField(auto_now_add=True)
	used = models.BooleanField(default=False)
	used_at = models.DateTimeField(null=True, blank=True)
	expires_at = models.DateTimeField(null=True, blank=True)

	def is_valid(self):
		if self.used:
			return False
		if self.expires_at and timezone.now() > self.expires_at:
			return False
		return True

	def __str__(self):
		return f"Token for {self.user} ({'used' if self.used else 'unused'})"


class Vote(models.Model):
	candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True)
	token_value = models.CharField(max_length=128, null=True, blank=True)

	def __str__(self):
		return f"Vote for {self.candidate} at {self.created_at}"
