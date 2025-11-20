# Generated migration for semantic_hash field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0003_alter_card_due_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='semantic_hash',
            field=models.CharField(
                max_length=32,
                db_index=True,
                editable=False,
                blank=True,
                verbose_name='语义指纹'
            ),
        ),
    ]
