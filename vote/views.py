def vote_result(request):
	# Render the modern vote result page
	return render(request, "vote/vote_result.html")

def voting_status_api(request):
	# Returns current voting status (open/closed)
	voting_status = VotingStatus.get_status()
	return JsonResponse({"voting_open": voting_status.is_open})

def landing_stats_api(request):
	# Returns stats for the landing page: joined, waiting, voted, and results
	from django.db.models import Count
	total_tokens = BallotToken.objects.count()
	voted_count = BallotToken.objects.filter(used=True).count()
	waiting_count = BallotToken.objects.filter(used=False).count()
	voter_count = total_tokens
	# Vote results per candidate
	results = list(
		Candidate.objects.annotate(votes=Count('vote')).values('name', 'votes').order_by('-votes', 'name')
	)
	# Voter list: show token and status
	voters = BallotToken.objects.all().order_by('-created_at')[:50]  # limit to last 50
	voter_list = [
		{
			"token": v.token,
			"status": "Voted" if v.used else "Waiting"
		} for v in voters
	]
	return JsonResponse({
		"voter_count": voter_count,
		"waiting_count": waiting_count,
		"voted_count": voted_count,
		"results": [
			{"candidate": r["name"], "votes": r["votes"]} for r in results
		],
		"voters": voter_list
	})
from django.http import JsonResponse
def voter_count_api(request):
	# Returns the number of voters who have joined (used their token)
	count = BallotToken.objects.filter(used=True).count()
	return JsonResponse({"voter_count": count})
def display_qr(request):
	# Generate and return a QR code image for the voting start URL
	start_url = request.build_absolute_uri('/vote/start/')
	qr = qrcode.QRCode(box_size=10, border=4)
	qr.add_data(start_url)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format='PNG')
	buf.seek(0)
	return HttpResponse(buf.getvalue(), content_type='image/png')

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from .models import BallotToken, Candidate, Vote, generate_token, VotingStatus
import qrcode
import io

@staff_member_required
def landing(request):
	# Render landing page with embedded QR code and admin voting control
	qr_url = request.build_absolute_uri('/vote/qr_img/')
	voting_status = VotingStatus.get_status()
	voting_open = voting_status.is_open
	if request.method == "POST":
		action = request.POST.get("action")
		if action == "open":
			voting_status.is_open = True
			voting_status.save()
		elif action == "close":
			voting_status.is_open = False
			voting_status.save()
		voting_open = voting_status.is_open
	return render(request, "vote/landing.html", {"qr_url": qr_url, "voting_open": voting_open})

import re

def is_mobile_device(request):
	"""Check if the request is from a mobile device based on User-Agent"""
	user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
	mobile_patterns = [
		'iphone', 'ipod', 'android', 'mobile', 'blackberry', 'windows phone',
		'opera mini', 'opera mobi', 'iemobile', 'webos', 'palm', 'symbian',
		'samsung', 'nokia', 'lg-', 'htc', 'sony', 'motorola', 'zte', 'huawei',
		'xiaomi', 'oppo', 'vivo', 'realme', 'oneplus'
	]
	return any(pattern in user_agent for pattern in mobile_patterns)

def get_client_ip(request):
	"""Get client IP address from request"""
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0].strip()
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip

def create_device_fingerprint(request):
	"""Create a device fingerprint hash from request data"""
	import hashlib
	from .models import DeviceFingerprint
	
	ip = get_client_ip(request)
	user_agent = request.META.get('HTTP_USER_AGENT', '')
	accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
	accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
	
	# Create fingerprint from multiple factors
	fingerprint_data = f"{ip}|{user_agent}|{accept_language}|{accept_encoding}"
	fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
	
	# Get or create device fingerprint record
	device, created = DeviceFingerprint.objects.get_or_create(
		fingerprint_hash=fingerprint_hash,
		defaults={
			'ip_address': ip,
			'user_agent': user_agent[:500] if user_agent else ''
		}
	)
	return device

def vote_start(request):
	# Only allow access from mobile devices (smartphones)
	if not is_mobile_device(request):
		return render(request, "vote/access_denied.html", {
			"message": "This page can only be accessed from a smartphone. Please scan the QR code with your mobile device."
		})
	
	# Check if this device has already voted (cookie check)
	if request.COOKIES.get('has_voted') == 'true':
		return render(request, "vote/already_voted.html", {
			"message": "You have already voted. Each person can only vote once."
		})
	
	# Check device fingerprint in database
	device = create_device_fingerprint(request)
	if device.has_voted:
		return render(request, "vote/already_voted.html", {
			"message": "This device has already been used to vote. Each device can only vote once."
		})
	
	# Generate a new token for this session, linked to device
	token = generate_token()
	BallotToken.objects.create(token=token, user=None, device_fingerprint=device)
	return redirect('vote_waiting', token=token)

def vote_waiting(request, token):
	# Show waiting page with unique code and join button
	return render(request, "vote/waiting.html", {"token": token})



def vote_view(request, token):
	# Main voting view: handles GET (show ballot) and POST (submit vote)
	ballot = get_object_or_404(BallotToken, token=token)
	voting_status = VotingStatus.get_status()
	voting_open = voting_status.is_open

	if not ballot.is_valid():
		return render(request, "vote/ballot.html", {"candidates": Candidate.objects.all(), "token": token, "voting_open": voting_open, "error": "This code is invalid or has already been used."})

	if not voting_open:
		return render(request, "vote/ballot.html", {"candidates": Candidate.objects.all(), "token": token, "voting_open": False})

	if request.method == "POST":
		candidate_id = request.POST.get("candidate")
		candidate = get_object_or_404(Candidate, pk=candidate_id)
		Vote.objects.create(candidate=candidate, token_value=ballot.token)
		ballot.used = True
		ballot.used_at = timezone.now()
		ballot.save()
		
		# Mark device fingerprint as having voted
		if ballot.device_fingerprint:
			ballot.device_fingerprint.has_voted = True
			ballot.device_fingerprint.save()
		
		# Set cookie to prevent voting again from this device
		response = render(request, "vote/thanks.html")
		response.set_cookie('has_voted', 'true', max_age=60*60*24*365, httponly=True, samesite='Lax')  # 1 year
		return response

	candidates = Candidate.objects.all()
	return render(request, "vote/ballot.html", {"candidates": candidates, "token": token, "voting_open": voting_open})
