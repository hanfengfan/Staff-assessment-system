# Generated manually to add ai_score field to ExamRecord model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_update_correct_answer_to_textfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='examrecord',
            name='ai_score',
            field=models.FloatField(
                blank=True,
                help_text='AI评分(0-100)，仅用于主观题',
                null=True,
                verbose_name='AI评分(0-100)'
            ),
        ),
    ]