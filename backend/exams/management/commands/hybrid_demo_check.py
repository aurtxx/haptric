import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from exams.models import Attempt, Exam, Organization, Result, Student, SyncOutbox


class Command(BaseCommand):
    help = "Validate the configured disposable LAN/Cloud hybrid demo node."

    def handle(self, *args, **options):
        node_id = os.getenv("HAPTRIC_NODE_ID", "").strip()
        node_role = os.getenv("HAPTRIC_NODE_ROLE", "").strip()
        if not node_id or node_role not in {"lan", "cloud"}:
            raise CommandError("HAPTRIC_NODE_ID and HAPTRIC_NODE_ROLE=lan|cloud are required")
        organization_id = os.getenv("HAPTRIC_SYNC_ORGANIZATION_ID", "").strip()
        if not organization_id:
            raise CommandError("HAPTRIC_SYNC_ORGANIZATION_ID is required")
        organization = Organization.objects.filter(id=organization_id).first()
        if not organization:
            raise CommandError("Configured organization is not present in this database")
        expected_exam = os.getenv("HAPTRIC_DEMO_EXAM_ID", "").strip()
        expected_student = os.getenv("HAPTRIC_DEMO_STUDENT_ID", "").strip()
        checks = {
            "database": str(connection.settings_dict.get("NAME")),
            "node_id": node_id,
            "node_role": node_role,
            "upstream_configured": bool(os.getenv("HAPTRIC_SYNC_URL")),
            "organization_id": str(organization.id),
            "reference_ids_aligned": True,
            "pending_events": SyncOutbox.objects.filter(organization=organization, delivery_status__in=[SyncOutbox.DeliveryStatus.PENDING, SyncOutbox.DeliveryStatus.FAILED]).count(),
            "conflict_events": SyncOutbox.objects.filter(organization=organization, delivery_status=SyncOutbox.DeliveryStatus.CONFLICT).count(),
            "attempts": Attempt.objects.filter(exam__organization=organization).count(),
            "results": Result.objects.filter(attempt__exam__organization=organization).count(),
        }
        if expected_exam and not Exam.objects.filter(id=expected_exam, organization=organization).exists():
            checks["reference_ids_aligned"] = False
        if expected_student and not Student.objects.filter(id=expected_student, organization=organization).exists():
            checks["reference_ids_aligned"] = False
        self.stdout.write(json.dumps(checks, sort_keys=True))
        if not checks["reference_ids_aligned"]:
            raise CommandError("Configured demo reference IDs are not aligned")
