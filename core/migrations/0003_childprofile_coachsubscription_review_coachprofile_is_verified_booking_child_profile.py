# Generated migration for LevelUp v2 new features:
#   - CoachSubscription (subscription tiers for coaches)
#   - ChildProfile (GDPR Article 8 — parent/child sub-profiles)
#   - Review (1-5 star post-session reviews)
#   - CoachProfile.is_verified (Garda vetting badge)
#   - Booking.child_profile (FK to ChildProfile, nullable)

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        # Depends on the two existing migrations already in the project
        ('core', '0002_booking_student_location'),
    ]

    operations = [
        # ── CoachSubscription ─────────────────────────────────────────────
        migrations.CreateModel(
            name='CoachSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', models.CharField(
                    choices=[('FREE', 'Free'), ('PRO', 'Pro – €59.95/year')],
                    default='FREE',
                    max_length=10,
                )),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('coach_user', models.OneToOneField(
                    limit_choices_to={'role': 'COACH'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subscription',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # ── ChildProfile ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='ChildProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forename', models.CharField(max_length=80)),
                ('surname', models.CharField(max_length=80)),
                ('dob', models.DateField(
                    help_text='Used to confirm the child is a minor (under 18).',
                )),
                ('year_group', models.CharField(
                    blank=True,
                    help_text='e.g. 5th Year, Leaving Cert, Junior Cert',
                    max_length=40,
                )),
                ('parent', models.ForeignKey(
                    limit_choices_to={'role': 'STUDENT'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='child_profiles',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # ── CoachProfile.is_verified ──────────────────────────────────────
        migrations.AddField(
            model_name='coachprofile',
            name='is_verified',
            field=models.BooleanField(
                default=False,
                help_text='Manually set by admin after identity/Garda vetting check.',
            ),
        ),

        # ── Booking.child_profile ─────────────────────────────────────────
        migrations.AddField(
            model_name='booking',
            name='child_profile',
            field=models.ForeignKey(
                blank=True,
                help_text='If set, the booking is on behalf of this child.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='bookings',
                to='core.childprofile',
            ),
        ),

        # ── Review ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stars', models.PositiveSmallIntegerField(
                    help_text='Rating from 1 (poor) to 5 (excellent).',
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(5),
                    ],
                )),
                ('comment', models.TextField(
                    blank=True,
                    help_text='Optional written feedback.',
                )),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('booking', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='review',
                    to='core.booking',
                )),
                ('coach', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reviews',
                    to='core.coachprofile',
                )),
            ],
        ),
    ]
