from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from django.conf import settings


def get_total_users():
    client = BetaAnalyticsDataClient.from_service_account_file(
        settings.GA_CREDENTIALS_FILE
    )

    request = RunReportRequest(
        property=f"properties/{settings.GA4_PROPERTY_ID}",
        metrics=[{"name": "totalUsers"}],
        date_ranges=[{"start_date": "2020-01-01", "end_date": "today"}],
    )

    response = client.run_report(request)

    return int(response.rows[0].metric_values[0].value)
