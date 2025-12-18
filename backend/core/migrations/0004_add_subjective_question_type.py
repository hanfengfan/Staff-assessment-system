# Generated manually for subjective question support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_role_category_to_tag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('single', '单选题'),
                    ('multiple', '多选题'),
                    ('true_false', '判断题'),
                    ('subjective', '主观题')
                ],
                default='single',
                max_length=20,
                verbose_name='题目类型'
            ),
        ),
    ]