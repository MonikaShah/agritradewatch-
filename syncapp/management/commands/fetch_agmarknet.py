import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from syncapp.models import WebData


API_KEY = "579b464db66ec23bdd000001299f96bce479493b5a2c48d965845885"
BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


class TLSAdapter(HTTPAdapter):
    """Adapter that enforces TLSv1.2+"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # ✅ correct enum
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class Command(BaseCommand):
    help = "Fetch commodity prices from Agmark (data.gov.in API for Maharashtra APMCs)"

    def handle(self, *args, **kwargs):
        start_date = "2025-08-11"
        end_date = timezone.localdate()

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = end_date

        session = requests.Session()
        session.mount("https://", TLSAdapter())

        commodities = ["Onion", "Tomato", "Potato", "Carrot", "Guava", "Pomegranate", "Drumstick"]

        total = 0
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y-%m-%d")

            for com in commodities:
                params = {
                    "api-key": API_KEY,
                    "format": "json",
                    "limit": 10000,
                    "filters[state]": "Maharashtra",
                    "filters[commodity]": com,
                    "filters[arrival_date]": date_str,
                }
                try:
                    r = session.get(BASE, params=params, timeout=60)
                    r.raise_for_status()
                    records = r.json().get("records", [])
                    self.stdout.write(f"✔ {len(records)} records fetched for {com} on {date_str}")
                except Exception as e:
                    self.stderr.write(f"✖ Error fetching {com} on {date_str}: {e}")
                    continue

                for rec in records:
                    try:
                        raw_date = rec.get("arrival_date")
                        arrival_date = None
                        if raw_date:
                            try:
                                arrival_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
                            except ValueError:
                                self.stderr.write(f"Invalid date format: {raw_date}")
                                continue

                        self.stdout.write(f"→ Inserting {rec.get('commodity')} {rec.get('variety')} on {arrival_date}...")

                        obj = WebData.objects.create(
                            source="agmark",
                            commodity=rec.get("commodity"),
                            variety=rec.get("variety"),
                            date=arrival_date,
                            minprice=self._to_int(rec.get("min_price")),
                            maxprice=self._to_int(rec.get("max_price")),
                            modalprice=self._to_int(rec.get("modal_price")),
                            apmc=rec.get("market"),
                        )

                        self.stdout.write(f"   ✔ Inserted ID={obj.id}")
                        total += 1

                        # force DB flush
                        transaction.on_commit(lambda: None)

                    except Exception as e:
                        self.stderr.write(f"✖ DB insert error for {rec}: {e}")
                        current_dt += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"Inserted {total} records from Agmark."))

    def _to_int(self, val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
