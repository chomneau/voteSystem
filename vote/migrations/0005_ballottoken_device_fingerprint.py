# Generated manually on 2026-01-12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0004_devicefingerprint'),
    ]

    operations = [
        migrations.AddField(
            model_name='ballottoken',
            name='device_fingerprint',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='vote.devicefingerprint'
            ),
        ),
    ]
