from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0006_supplieragency_supplierguide'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplieragency',
            name='name_initials',
            field=models.CharField(
                verbose_name='名字拼音首字母',
                max_length=128,
                blank=True,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='supplierguide',
            name='name_initials',
            field=models.CharField(
                verbose_name='名字拼音首字母',
                max_length=128,
                blank=True,
                db_index=True,
            ),
        ),
    ]

