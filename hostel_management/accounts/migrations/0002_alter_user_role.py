from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('student', 'Student'), ('admin', 'Admin'), ('warden', 'Warden')],
                default='student',
                max_length=10,
            ),
        ),
    ]
