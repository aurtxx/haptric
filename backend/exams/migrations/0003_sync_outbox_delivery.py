from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [("exams", "0002_exam_schedule")]

    operations = [
        migrations.AddField(
            model_name="syncoutbox",
            name="delivery_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("delivered", "Delivered"), ("failed", "Failed"), ("conflict", "Conflict")],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(model_name="syncoutbox", name="delivered_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="syncoutbox", name="last_error", field=models.CharField(blank=True, default="", max_length=500)),
        migrations.AddField(model_name="syncoutbox", name="origin_node", field=models.CharField(default="local", max_length=120)),
        migrations.AddField(model_name="syncoutbox", name="occurred_at", field=models.DateTimeField(default=timezone.now)),
        migrations.AddField(model_name="syncoutbox", name="schema_version", field=models.PositiveIntegerField(default=1)),
    ]
