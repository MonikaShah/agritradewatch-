import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
from django.utils import timezone
from syncapp.models import WebData, Commodity


class Command(BaseCommand):
    help = "Fetch Agrowon daily crop prices and insert/update WebData table"

    AGROWON_URL = "https://agrowon.esakal.com/feapi/msamb"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date', type=str, help="Start date in YYYY-MM-DD format", required=False
        )
        parser.add_argument(
            '--end_date', type=str, help="End date in YYYY-MM-DD format", required=False
        )

    def parse_agrowon_date(self, date_str):
        """Parse Agrowon date string to Django timezone-aware datetime."""
        if not date_str:
            self.stdout.write("DEBUG: Empty r_date received")
            return None
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            try:
                dt = datetime.strptime(date_str, "%d-%m-%Y")
            except Exception as e:
                self.stderr.write(f"Failed to parse date '{date_str}': {e}")
                return None
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt

    def safe_int(self, val):
        """Safely convert a string to int, removing commas/spaces."""
        if not val:
            return None
        try:
            return int(val.replace(',', '').strip())
        except Exception:
            return None

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
        self.stdout.write(f"DEBUG: Sending request to Agrowon for {date_str}")
        resp = requests.post(self.AGROWON_URL, data=soap_body.encode("utf-8"), headers=headers)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            self.stderr.write(f"Failed HTTP request for {date_str}: {resp.status_code}")
            return []

        try:
            root = ET.fromstring(resp.text)
        except Exception as e:
            self.stderr.write(f"Failed to parse XML for {date_str}: {e}")
            return []

        records = []
        for msamb_data in root.iter("msamb_data"):
            record = {
                tag: (msamb_data.find(tag).text if msamb_data.find(tag) is not None else "")
                for tag in ["r_date", "comm_name", "apmc_name", "variety_name", "unit", "arrivals", "min", "max", "Model"]
            }
            records.append(record)
        self.stdout.write(f"DEBUG: Found {len(records)} records for {date_str}")
        return records

    def handle(self, *args, **options):
        start_date_str = options.get('start_date')
        end_date_str = options.get('end_date')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime(2025, 8, 11).date()

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = timezone.localdate()

        start_date = timezone.make_aware(datetime.combine(start_date, time.min))
        end_date = timezone.make_aware(datetime.combine(end_date, time.min))

        self.stdout.write(f"DEBUG: Processing from {start_date} to {end_date}")

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

            if not records:
                self.stdout.write(f"No records found for {current_date.strftime('%d-%m-%Y')}")
                current_date += timedelta(days=1)
                continue

            count = 0
            for rec in records:
                self.stdout.write(f"DEBUG: Processing record: {rec}")
                commodity_obj = Commodity.objects.filter(alias_marathi=rec["comm_name"]).first()
                if not commodity_obj:
                    self.stdout.write(f"Skipping: Commodity '{rec['comm_name']}' not found in Commodity table")
                    continue

                record_date = self.parse_agrowon_date(rec["r_date"])
                if not record_date:
                    self.stdout.write(f"Skipping: Invalid date for record {rec}")
                    continue

                try:
                    obj, created = WebData.objects.update_or_create(
                        source="agrowon",
                        commodity=rec["comm_name"],
                        variety=rec.get("variety_name", ""),
                        apmc=rec.get("apmc_name", ""),
                        date=record_date,
                        defaults={
                            "minprice": self.safe_int(rec.get("min")),
                            "maxprice": self.safe_int(rec.get("max")),
                            "modalprice": self.safe_int(rec.get("Model")),
                            "unit": rec.get("unit", ""),
                        }
                    )
                    count += 1
                    action = "Created" if created else "Updated"
                    self.stdout.write(f"{action}: {obj}")
                except Exception as e:
                    self.stderr.write(f"Error inserting/updating record {rec}: {e}")

            self.stdout.write(self.style.SUCCESS(f"Inserted/Updated {count} records for {current_date.strftime('%d-%m-%Y')}"))
            total_count += count
            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"Total records inserted/updated: {total_count}"))
import requests
import psycopg2
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# ----------------------------
# SSL/TLS Adapter to handle server SSL issues
# ----------------------------
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        # Enable legacy SSL/TLS options (if server uses old TLS)
        context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# ----------------------------
# Database connection
# ----------------------------
conn = psycopg2.connect(
    dbname="agritradewatch",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# ----------------------------
# API fetch function
# ----------------------------
def fetch_data(date):
    url = "https://agrowon.esakal.com/feapi/msamb"  # API URL
    session = requests.Session()
    session.mount('https://', TLSAdapter())

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()  # assuming JSON response
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for {date}: {e}")
        return None

# ----------------------------
# Insert function
# ----------------------------
def insert_data(data):
    if not data:
        return

    for record in data:
        # Customize columns according to your webdata table
        cursor.execute("""
            INSERT INTO webdata (column1, column2, column3)
            VALUES (%s, %s, %s)
        """, (
            record.get('field1'),
            record.get('field2'),
            record.get('field3')
        ))
    conn.commit()
    print(f"Inserted {len(data)} records successfully.")

# ----------------------------
# Main script
# ----------------------------
date = "2025-09-17"  # example date
data = fetch_data(date)
insert_data(data)

cursor.close()
conn.close()
