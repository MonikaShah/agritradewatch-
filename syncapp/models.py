# Create your models here.
from django.contrib.gis.db import models


# class Consumer(models.Model):
#     id = models.CharField(max_length=100, primary_key=True)
#     name = models.CharField(max_length=255, null=True, blank=True)
#     geom = models.PointField(null=True, blank=True)
#     data = models.JSONField(null=True, blank=True)
class Consumer(models.Model):
    id = models.CharField(primary_key=True, max_length=50)  # Firebase ID
    name = models.CharField(max_length=200)                  # commodity name
    user_id = models.CharField(max_length=200, db_index=True)
    price_per_unit = models.FloatField(default=0)
    quantity = models.FloatField(default=0)
    geom = models.PointField(blank=True, null=True)      # PostGIS Point
    date = models.DateTimeField(blank=True, null=True)       # Firestore date
    timestamp = models.BigIntegerField(blank=True, null=True)  # raw Firestore timestamp
    created_at = models.DateTimeField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    product = models.CharField(max_length=100, null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)



    def __str__(self):
        return f"{self.name} ({self.user_id})"
# syncapp/models.py




class Farmer(models.Model):
    id = models.CharField(primary_key=True, max_length=50)  # Firebase ID
    name = models.CharField(max_length=255)  # farmer name (if present in Firebase)
    product = models.CharField(max_length=255, blank=True, null=True)  # <-- add this
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # total available
    unit = models.CharField(max_length=50, null=True, blank=True)   # Add this
    geom = models.PointField(null=True, blank=True)     
    location = models.CharField(max_length=255, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.BigIntegerField(null=True, blank=True)       # Firestore timestamp


    def __str__(self):
        return f"{self.name} - {self.product} ({self.price_per_unit}/{self.unit})"

# class Farmer(models.Model):
#     id = models.CharField(max_length=100, primary_key=True)
#     name = models.CharField(max_length=255, null=True, blank=True)
#     geom = models.PointField(null=True, blank=True)
#     # data = models.JSONField(blank=True, null=True)  # Add this field to store Firestore data


# class UserData(models.Model):
#     id = models.CharField(max_length=100, primary_key=True)
#     data = models.JSONField()
class UserData(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=100)
    lat = models.FloatField()
    lng = models.FloatField()
    product = models.CharField(max_length=100)
    quantity = models.FloatField()
    unit = models.CharField(max_length=50)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.product}"


class MarketPrices(models.Model):
    arrival_date = models.DateField()
    market = models.CharField(max_length=100)

    commodity = models.CharField(max_length=100)
    variety = models.CharField(max_length=100)
    min_price = models.FloatField()
    max_price = models.FloatField()
    modal_price = models.FloatField()
    source = models.CharField(max_length=100)
    id = models.CharField(max_length=100, primary_key=True)


    def __str__(self):
        return f"{self.commodity} ({self.variety}) at {self.market} on {self.arrival_date}"
    

    class Meta:
        db_table = 'market_prices'
        
