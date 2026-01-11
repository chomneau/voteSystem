from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vote.models import BallotToken
from django.utils import timezone
from datetime import timedelta
import qrcode
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Generate ballot tokens and QR codes for a list of usernames"

    def add_arguments(self, parser):
        parser.add_argument("--usernames", nargs="+", help="List of usernames", required=True)
        parser.add_argument("--outdir", default="qrcodes", help="Output directory for QR images")
        parser.add_argument("--expire-days", type=int, default=7)

    def handle(self, *args, **options):
        outdir = options["outdir"]
        os.makedirs(outdir, exist_ok=True)
        for username in options["usernames"]:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(f"User {username} not found, skipping.")
                continue
            token = BallotToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(days=options["expire_days"])
            )
            link = f"http://localhost:8000/vote/{token.token}/"
            img = qrcode.make(link)
            path = os.path.join(outdir, f"{username}.png")
            img.save(path)
            self.stdout.write(f"Created token for {username}: {path}")
