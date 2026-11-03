from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("exams", "0001_initial")]
    operations = [
        migrations.AddField(model_name="exam", name="available_from", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="exam", name="available_until", field=models.DateTimeField(blank=True, null=True)),
    ]
