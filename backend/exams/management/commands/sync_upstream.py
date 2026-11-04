import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from django.utils import timezone

from exams.models import SyncOutbox


class Command(BaseCommand):
    help = "Push pending Haptric sync events to the configured upstream node."

    def handle(self, *args, **options):
        url = os.getenv("HAPTRIC_SYNC_URL", "").strip()
        token = os.getenv("HAPTRIC_SYNC_TOKEN", "").strip()
        if not url or not token:
            self.stderr.write("HAPTRIC_SYNC_URL and HAPTRIC_SYNC_TOKEN are required")
            return
        org_id = SyncOutbox.objects.values_list("organization_id", flat=True).first()
        if not org_id:
            self.stdout.write("No organization events pending")
            return
        qs = SyncOutbox.objects.filter(organization_id=org_id, delivery_status__in=[SyncOutbox.DeliveryStatus.PENDING, SyncOutbox.DeliveryStatus.FAILED]).order_by("created_at")[:100]
        events = []
        for event in qs:
            event.attempts += 1
            event.save(update_fields=["attempts"])
            events.append({
                "event_id": str(event.id),
                "event_type": event.event_type,
                "organization_id": str(event.organization_id),
                "origin_node": event.origin_node,
                "aggregate_type": event.entity_type,
                "aggregate_id": event.entity_id,
                "occurred_at": event.occurred_at.isoformat(),
                "schema_version": event.schema_version,
                "idempotency_key": event.idempotency_key,
                "payload": event.payload,
            })
        if not events:
            self.stdout.write("No pending events")
            return
        body = json.dumps({"organization_id": str(org_id), "events": events}).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json", "X-Haptric-Sync-Token": token}, method="POST")
        try:
            with urlopen(request, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            SyncOutbox.objects.filter(id__in=[event["event_id"] for event in events]).update(delivery_status=SyncOutbox.DeliveryStatus.FAILED, last_error=str(exc)[:500])
            self.stderr.write(f"Upstream unavailable; retained {len(events)} events: {exc}")
            return
        accepted = set(result.get("accepted_event_ids", []))
        conflicts = set(result.get("conflicts", []))
        for event in events:
            event_id = event["event_id"]
            if event_id in conflicts:
                SyncOutbox.objects.filter(id=event_id).update(delivery_status=SyncOutbox.DeliveryStatus.CONFLICT, last_error="upstream conflict")
            elif event_id in accepted:
                SyncOutbox.objects.filter(id=event_id).update(delivery_status=SyncOutbox.DeliveryStatus.DELIVERED, processed_at=timezone.now(), delivered_at=timezone.now(), last_error="")
        self.stdout.write(f"Accepted {len(accepted)}; conflicts {len(conflicts)}")
