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
        configured = os.getenv("HAPTRIC_SYNC_ORGANIZATION_ID", "").strip()
        configured_many = [item.strip() for item in os.getenv("HAPTRIC_SYNC_ORGANIZATION_IDS", "").split(",") if item.strip()]
        allowed = set(configured_many or ([configured] if configured else []))
        organizations = SyncOutbox.objects.filter(
            delivery_status__in=[SyncOutbox.DeliveryStatus.PENDING, SyncOutbox.DeliveryStatus.FAILED],
            available_at__lte=timezone.now(),
        ).values_list("organization_id", flat=True).distinct()
        if allowed:
            organizations = [org_id for org_id in organizations if str(org_id) in allowed]
        else:
            organizations = list(organizations)
        if not organizations:
            self.stdout.write("No pending events")
            return
        for org_id in organizations:
            self._sync_organization(url, token, org_id)

    def _sync_organization(self, url, token, org_id):
        queryset = SyncOutbox.objects.filter(
            organization_id=org_id,
            delivery_status__in=[SyncOutbox.DeliveryStatus.PENDING, SyncOutbox.DeliveryStatus.FAILED],
            available_at__lte=timezone.now(),
        ).order_by("created_at")[:100]
        events = []
        for event in queryset:
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
            return
        body = json.dumps({"organization_id": str(org_id), "events": events}).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json", "X-Haptric-Sync-Token": token}, method="POST")
        try:
            with urlopen(request, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            SyncOutbox.objects.filter(id__in=[event["event_id"] for event in events]).update(
                delivery_status=SyncOutbox.DeliveryStatus.FAILED,
                last_error=str(exc)[:500],
                available_at=timezone.now(),
            )
            self.stderr.write(f"organization={org_id} upstream unavailable; retained {len(events)} events")
            return
        accepted = set(result.get("accepted_event_ids", []))
        conflicts = set(result.get("conflicts", []))
        now = timezone.now()
        for event in events:
            event_id = event["event_id"]
            if event_id in conflicts:
                SyncOutbox.objects.filter(id=event_id).update(delivery_status=SyncOutbox.DeliveryStatus.CONFLICT, last_error="upstream conflict", available_at=now)
            elif event_id in accepted:
                SyncOutbox.objects.filter(id=event_id).update(delivery_status=SyncOutbox.DeliveryStatus.DELIVERED, processed_at=now, delivered_at=now, last_error="", available_at=now)
        self.stdout.write(f"organization={org_id} accepted={len(accepted)} conflicts={len(conflicts)}")
