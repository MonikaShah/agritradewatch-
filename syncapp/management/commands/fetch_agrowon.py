import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
from django.utils import timezone
from syncapp.models import WebData, Commodity  # adjust if your app is named differently


class Command(BaseCommand):
    help = "Fetch Agrowon daily crop prices and insert/update WebData table"

    AGROWON_URL = "https://agrowon.esakal.com/feapi/msamb"

    def parse_agrowon_date(self, date_str):
        """Parse Agrowon date string to Django timezone-aware datetime."""
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            dt = datetime.strptime(date_str, "%d-%m-%Y")
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt

    def fetch_data_for_date(self, date_obj):
        date_str = date_obj.strftime("%d-%m-%Y")
        soap_body = f"""
        <?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                         xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                         xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
          <soap12:Body>
            <get_selected_data xmlns="http://tempuri.org/">
              <from_date>{date_str}</from_date>
              <to_date>{date_str}</to_date>
            </get_selected_data>
          </soap12:Body>
        </soap12:Envelope>
        """

        headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
        resp = requests.post(self.AGROWON_URL, data=soap_body.encode("utf-8"), headers=headers)
        resp.encoding = "utf-8"

        root = ET.fromstring(resp.text)
        records = []
        for msamb_data in root.iter("msamb_data"):
            record = {
                tag: (msamb_data.find(tag).text if msamb_data.find(tag) is not None else "")
                for tag in ["r_date", "comm_name", "apmc_name", "variety_name", "unit", "arrivals", "min", "max", "Model"]
            }
            records.append(record)
        return records

    def handle(self, *args, **kwargs):
        start_date = datetime(2025, 8, 11)  # Replace with your desired past start date
        start_date = timezone.make_aware(start_date)  # now aware

        end_date = timezone.localdate()  # date object
        end_date = timezone.make_aware(datetime.combine(end_date, time.min))  # aware datetime at midnight

        current_date = start_date
        total_count = 0
        while current_date <= end_date:
            self.stdout.write(f"Fetching Agrowon data for {current_date.strftime('%d-%m-%Y')}")
            try:
                records = self.fetch_data_for_date(current_date)
            except Exception as e:
                self.stderr.write(f"Failed to fetch data for {current_date}: {e}")
                current_date += timedelta(days=1)
                continue

            count = 0
            for rec in records:
                commodity_obj = Commodity.objects.filter(alias_marathi=rec["comm_name"]).first()
                if not commodity_obj:
                    continue  # skip crops not in Commodity table

                try:
                    WebData.objects.update_or_create(
                        source="agrowon",
                        commodity=rec["comm_name"],
                        variety=rec.get("variety_name", ""),
                        apmc=rec.get("apmc_name", ""),
                        date=self.parse_agrowon_date(rec["r_date"]),
                        defaults={
                            "minprice": int(rec["min"]) if rec["min"].isdigit() else None,
                            "maxprice": int(rec["max"]) if rec["max"].isdigit() else None,
                            "modalprice": int(rec["Model"]) if rec["Model"].isdigit() else None,
                            "unit": rec.get("unit", ""),
                        }
                    )
                    count += 1
                except Exception as e:
                    self.stderr.write(f"Error inserting record {rec}: {e}")

            self.stdout.write(self.style.SUCCESS(f"Inserted/Updated {count} records for {current_date.strftime('%d-%m-%Y')}"))
            total_count += count
            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"Total records inserted/updated: {total_count}"))
