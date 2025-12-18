# Generated manually for updating correct_answer to TextField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_subjective_question_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='correct_answer',
            field=models.TextField(
                help_text='单选题填字母，多选题用逗号分隔，判断题填True/False，主观题填写参考答案或评分标准',
                verbose_name='正确答案/参考答案'
            ),
        ),
        migrations.AlterField(
            model_name='question',
            name='options',
            field=models.JSONField(
                blank=True,
                help_text='JSON格式，示例: [{"key": "A", "text": "选项内容"}]，主观题可为空或填写答题提示',
                null=True,
                verbose_name='选项列表'
            ),
        ),
    ]