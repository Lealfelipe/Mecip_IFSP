from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0027_referenceattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='indicator',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
