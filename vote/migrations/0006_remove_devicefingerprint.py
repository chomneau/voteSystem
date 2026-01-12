# Generated manually on 2026-01-12 - Remove DeviceFingerprint feature

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0005_ballottoken_device_fingerprint'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ballottoken',
            name='device_fingerprint',
        ),
        migrations.DeleteModel(
            name='DeviceFingerprint',
        ),
    ]
