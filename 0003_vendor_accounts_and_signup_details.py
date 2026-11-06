import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('market', '0002_securedatamodel'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='vendor',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vendor_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signup_request', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='first_name',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='last_name',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='business_name',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='contact_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='address',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
