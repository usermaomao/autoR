# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0004_card_semantic_hash'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='reviewlog',
            index=models.Index(fields=['user', 'reviewed_at'], name='cards_revie_user_id_review_idx'),
        ),
    ]

