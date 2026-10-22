from django.db import migrations, models


def fill_name(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.filter(name=''):
        user.name = f"{user.first_name}{user.last_name}".strip()
        user.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='department',
            new_name='station',
        ),
        migrations.AlterField(
            model_name='user',
            name='station',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='所属车站'),
        ),
        migrations.AddField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='姓名'),
        ),
        migrations.AddField(
            model_name='user',
            name='zone',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='所属站区'),
        ),
        migrations.AddField(
            model_name='user',
            name='extra',
            field=models.JSONField(blank=True, default=dict, help_text='预留的扩展字段，如入职日期、证书等', verbose_name='扩展信息'),
        ),
        migrations.RunPython(fill_name, migrations.RunPython.noop),
    ]
