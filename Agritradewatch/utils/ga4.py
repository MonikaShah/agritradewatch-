import os
from django.conf import settings
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.oauth2 import service_account

GA_CREDENTIALS = os.path.join(settings.BASE_DIR, "credentials/ga-service-account.json")
GA4_PROPERTY_ID = "519107243"

credentials = service_account.Credentials.from_service_account_file(GA_CREDENTIALS)
client = BetaAnalyticsDataClient(credentials=credentials)

def get_total_users():
    """
    Returns total active users from GA4
    """
    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[DateRange(start_date="2021-01-01", end_date="yesterday")],
        metrics=[Metric(name="totalUsers")],
    )
    response = client.run_report(request)
    return int(response.rows[0].metric_values[0].value)
