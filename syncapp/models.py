# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from ckeditor.fields import RichTextField
import uuid


# class Consumer(models.Model):
#     id = models.CharField(primary_key=True, max_length=50)  # Firebase ID
#     name = models.CharField(max_length=200)                  # commodity name
#     user_id = models.CharField(max_length=200, db_index=True)
#     price_per_unit = models.FloatField(default=0)
#     quantity = models.FloatField(default=0)
#     geom = models.PointField(blank=True, null=True)      # PostGIS Point
#     date = models.DateTimeField(blank=True, null=True)       # Firestore date
#     timestamp = models.BigIntegerField(blank=True, null=True)  # raw Firestore timestamp
#     created_at = models.DateTimeField(blank=True, null=True)
#     image = models.URLField(blank=True, null=True)
#     lat = models.FloatField(null=True, blank=True)
#     lng = models.FloatField(null=True, blank=True)
#     product = models.CharField(max_length=100, null=True, blank=True)
#     unit = models.CharField(max_length=50, null=True, blank=True)



#     def __str__(self):
#         return f"{self.name} ({self.user_id})"

# class Farmer(models.Model):
#     id = models.CharField(primary_key=True, max_length=50)  # Firebase ID
#     name = models.CharField(max_length=255)  # farmer name (if present in Firebase)
#     product = models.CharField(max_length=255, blank=True, null=True)  # <-- add this
#     price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # total available
#     unit = models.CharField(max_length=50, null=True, blank=True)   # Add this
#     geom = models.PointField(null=True, blank=True)     
#     location = models.CharField(max_length=255, null=True, blank=True)
#     lat = models.FloatField(null=True, blank=True)
#     lng = models.FloatField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     timestamp = models.BigIntegerField(null=True, blank=True)       # Firestore timestamp


#     def __str__(self):
#         return f"{self.name} - {self.product} ({self.price_per_unit}/{self.unit})"

# class UserData(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     timestamp = models.DateTimeField(null=True, blank=True)
#     name = models.CharField(max_length=100)
#     lat = models.FloatField()
#     lng = models.FloatField()
#     product = models.CharField(max_length=100)
#     quantity = models.FloatField()
#     unit = models.CharField(max_length=50)
#     price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.name} - {self.product}"


# class MarketPrices(models.Model):
#     arrival_date = models.DateField()
#     market = models.CharField(max_length=100)

#     commodity = models.CharField(max_length=100)
#     variety = models.CharField(max_length=100)
#     min_price = models.FloatField()
#     max_price = models.FloatField()
#     modal_price = models.FloatField()
#     source = models.CharField(max_length=100)
#     id = models.CharField(max_length=100, primary_key=True)


#     def __str__(self):
#         return f"{self.commodity} ({self.variety}) at {self.market} on {self.arrival_date}"
    

#     class Meta:
#         db_table = 'market_prices'

# class User1Manager(BaseUserManager):
#     def create_user(self, username, mobile=None, password=None, **extra_fields):
#         if not username:
#             raise ValueError("The Username is required")
#         user = self.model(username=username, mobile=mobile, **extra_fields)
#         user.set_password(password)  # stores a hashed password
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, password=None, **extra_fields):
#         extra_fields.setdefault("is_staff", True)
#         extra_fields.setdefault("is_superuser", True)
#         return self.create_user(username, password=password, **extra_fields)


class User1(AbstractUser):
    id = models.CharField(primary_key=True, max_length=50)  # Firebase UID as string
    name = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True, unique=True)
    job = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Needed for admin login

    # Make username non-nullable
    username = models.CharField(max_length=150, unique=True, null=False, blank=False)

    USERNAME_FIELD = 'username'  # keep login by username (or change to email/mobile if needed)
    REQUIRED_FIELDS = ['email', 'mobile']

    def __str__(self):
        return self.username
    # def has_perm(self, perm, obj=None):
    #     return self.is_staff  # minimal implementation for admin

    # def has_module_perms(self, app_label):
    #     return self.is_staff
    
    # Remove groups and permissions fields
    # groups = None
    # user_permissions = None

    class Meta:
        db_table = "syncapp_users1"

# -------------------------------
# Farmer model
# -------------------------------
class Farmer1(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    commodity = models.CharField(max_length=100)
    sellingprice = models.IntegerField(blank=True, null=True)
    receipt = models.TextField(blank=True, null=True)
    quantitysold = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'syncapp_farmers1'


# -------------------------------
# Consumer model
# -------------------------------
class Consumer1(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    commodity = models.CharField(max_length=100)
    buyingprice = models.IntegerField(blank=True, null=True)
    quantitybought = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    userid=models.CharField(max_length=100)

    class Meta:
        db_table = 'syncapp_consumers1'
  

class Commodity(models.Model):
    TYPE_CHOICES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('pulse', 'Pulse'),
    ]

    name = models.CharField(max_length=255, unique=True)
    alias_marathi = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    def __str__(self):
        return self.name
    class Meta:
        db_table = "commodity"
        managed = False  # keep this as False

# -------------------------------
# Webdata model
# -------------------------------
class WebData(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=100)
    commodity = models.CharField(max_length=255)  # store alias_marathi directly
    variety = models.CharField(max_length=100, blank=True, null=True)
    apmc = models.CharField(max_length=100, blank=True, null=True)
    minprice = models.IntegerField(blank=True, null=True)
    maxprice = models.IntegerField(blank=True, null=True)
    modalprice = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "webdata"
        managed = False
        unique_together = ("source", "commodity", "variety", "apmc", "date")

    

class Page(models.Model):
    STATUS_CHOICES = (
        (True, 'Active'),
        (False, 'Inactive'),
    )

    slug = models.SlugField(unique=True, help_text="URL-friendly unique identifier, e.g., 'about-us'")
    title = models.CharField(max_length=255)
    content = RichTextField(help_text="Page content with formatting (bold, bullets, images, etc.)")
    image = models.ImageField(upload_to='page_images/', blank=True, null=True)  # ✅ New field
    status = models.BooleanField(default=True, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pages"
        managed = False  # keep this as False
        ordering = ['title']
        verbose_name = "Page"
        verbose_name_plural = "Pages"

    def __str__(self):
        return self.title
  