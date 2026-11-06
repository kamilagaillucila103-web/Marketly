from django.db import migrations, models


def create_default_payment_channels(apps, schema_editor):
    PaymentChannel = apps.get_model('market', 'PaymentChannel')
    for method in ('GCASH', 'MAYA', 'BANK', 'CASH'):
        PaymentChannel.objects.get_or_create(method=method)


class Migration(migrations.Migration):
    dependencies = [
        ('market', '0005_rename_requested_at_signuprequest_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lease',
            name='monthly_rent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='lease',
            name='due_day',
            field=models.PositiveSmallIntegerField(default=5, help_text='Day of the month when rent is due (1-28 recommended).'),
        ),
        migrations.AlterField(
            model_name='vendorpayment',
            name='payment_type',
            field=models.CharField(choices=[('GCASH', 'GCash'), ('MAYA', 'Maya'), ('BANK', 'Bank Transfer'), ('CASH', 'Cash Payment')], default='GCASH', max_length=20),
        ),
        migrations.CreateModel(
            name='PaymentChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(choices=[('GCASH', 'GCash'), ('MAYA', 'Maya'), ('BANK', 'Bank Transfer'), ('CASH', 'Cash Payment')], max_length=20, unique=True)),
                ('account_name', models.CharField(blank=True, max_length=150)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('instructions', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['method']},
        ),
        migrations.RunPython(create_default_payment_channels, migrations.RunPython.noop),
    ]
