from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mecip', '0028_question_indicator'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='special_condition',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
