from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('mecip', '0026_user_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferenceAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('file', models.FileField(upload_to='reference_attachments/')),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
