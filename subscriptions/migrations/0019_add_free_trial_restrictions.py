# Generated migration for free trial restrictions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0018_booking_physical_only'),
    ]

    operations = [
        # Add new fields to UserSubscription for tracking trial usage
        migrations.AddField(
            model_name='usersubscription',
            name='legal_ed_subtopics_viewed',
            field=models.IntegerField(default=0, help_text="Number of legal education subtopics viewed (for trial limit)"),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='viewed_subtopic_ids',
            field=models.JSONField(default=list, help_text="List of subtopic IDs user has viewed", blank=True),
        ),
        
        # Add new feature flags to SubscriptionPlan for granular control
        migrations.AddField(
            model_name='subscriptionplan',
            name='can_comment_in_forums',
            field=models.BooleanField(default=True, help_text="Can user comment/reply in forums and hubs"),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='can_download_documents',
            field=models.BooleanField(default=True, help_text="Can user download generated documents"),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='can_talk_to_lawyer',
            field=models.BooleanField(default=True, help_text="Can user access Talk to Lawyer feature"),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='can_ask_questions_qa',
            field=models.BooleanField(default=True, help_text="Can user ask questions in Q&A"),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='can_book_consultation',
            field=models.BooleanField(default=True, help_text="Can user book consultations"),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='legal_ed_subtopics_limit',
            field=models.IntegerField(default=0, help_text="Max subtopics in Legal Education (0 = unlimited)"),
        ),
    ]
