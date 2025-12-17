# Create your models here.
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from ckeditor.fields import RichTextField
import uuid,os
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from PIL import Image


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
from django.core.exceptions import ValidationError

def validate_media_file(value):
    allowed_types = ["image/jpeg", "image/png", "video/mp4", "video/quicktime", "video/webm"]
    max_size_mb = 20

    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

    content_type = getattr(value.file, "content_type", "").lower()
    if content_type not in allowed_types:
        raise ValidationError(f"Unsupported file format. Allowed: {', '.join(allowed_types)}")

def validate_audio_file(value):
    allowed_types = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/wave", "audio/ogg", "audio/webm"]
    max_size_mb = 20

    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

    content_type = getattr(value.file, "content_type", "").lower()
    if content_type not in allowed_types:
        raise ValidationError(f"Unsupported file format. Allowed: {', '.join(allowed_types)}")



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
    email = models.EmailField(unique=True, blank=False, null=False)
    USERNAME_FIELD = 'username'  # keep login by username (or change to email/mobile if needed)
    REQUIRED_FIELDS = ['email', 'mobile']
    profile_pic = models.ImageField(
        upload_to='user_profile_upload/',
        null=True,
        blank=True
    )
    
    # Keep these so admin does not break
    groups = models.ManyToManyField(Group, blank=True, related_name="custom_user_set")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="custom_user_set")


    def __str__(self):
        return self.username
    # def has_perm(self, perm, obj=None):
    #     return self.is_staff  # minimal implementation for admin

    # def has_module_perms(self, app_label):
    #     return self.is_staff
    
    
    class Meta:
        db_table = "syncapp_users1"
        managed = True

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
    image = models.ImageField(upload_to="farmer_images/", blank=True, null=True)  
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    userid=models.CharField(max_length=100)

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
    image = models.ImageField(upload_to="consumer_images/", blank=True, null=True)  

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
    commodity_local = models.CharField(max_length=100, blank=True, null=True)  # Hindi/Marathi
    variety = models.CharField(max_length=100, blank=True, null=True)
    apmc = models.CharField(max_length=100, blank=True, null=True)
    minprice = models.IntegerField(blank=True, null=True)
    maxprice = models.IntegerField(blank=True, null=True)
    modalprice = models.IntegerField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    grade = models.CharField(max_length=20, blank=True, null=True)
    class Meta:
        db_table = "webdata"
        managed = True
        # unique_together = ("source", "commodity", "variety", "apmc", "date")

    def __str__(self):
        return f"{self.date} - {self.commodity} ({self.apmc})"

class Page(models.Model):
    STATUS_CHOICES = (
        (True, 'Active'),
        (False, 'Inactive'),
    )

    slug = models.SlugField(unique=True, help_text="URL-friendly unique identifier, e.g., 'about-us'")
    title = models.CharField(max_length=255)
    content = RichTextField(help_text="Page content with formatting (bold, bullets, images, etc.)")
    image = models.ImageField(upload_to='page_images/', blank=True, null=True)  #   New field
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
  

class APMC_Master(models.Model):
    apmc_name = models.CharField(max_length=150, primary_key=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "apmc_master"
        verbose_name = "APMC Master"
        verbose_name_plural = "APMC Masters"

    def __str__(self):
        return self.apmc_name


class APMC_Market_Prices(models.Model):
    market_name = models.ForeignKey(APMC_Master, on_delete=models.CASCADE, to_field='apmc_name',db_column='market_name', related_name='market_prices')
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    variety = models.CharField(max_length=150, null=True, blank=True)
    crop_group = models.CharField(max_length=100, null=True, blank=True)
    arrival_tonn = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_price_quintal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price_quintal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    modal_price_quintal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    report_date = models.DateField()
    grade = models.CharField(max_length=50, null=True, blank=True)
    commodity = models.CharField(max_length=100)
    class Meta:
        db_table ="apmc_market_prices"
        verbose_name = "APMC Market Price"
        verbose_name_plural = "APMC Market Prices"
        indexes = [
            models.Index(fields=['report_date']),
            models.Index(fields=['district']),
        ]

    def __str__(self):
        return f"{self.market_name} - {self.report_date}"

PLACE_DAMAGE_CHOICES = [
    ('on_field', 'On Field'),
    ('on_market', 'On Market'),
]
DAMAGE_UNITS=[
    ('ACRES','ACRES'),
    ('TONN','TONN')
]
class DamageCrop(models.Model):
    
    commodity = models.CharField(max_length=100,null = False)
    damage = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    unit = models.CharField(max_length=20,choices=DAMAGE_UNITS, default='ACRES')
    damage_date = models.DateField(blank=True, null=True)
    report_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    userid = models.ForeignKey('User1', models.DO_NOTHING,  blank=True, null=True)
    place_damage = models.CharField(max_length=20, choices=PLACE_DAMAGE_CHOICES,default='on_field')
    photo = models.ImageField(upload_to="damage_crop_images/", null=False, blank=False)  
    # district = models.CharField(max_length=100, blank=True, null=True)
    # tehsil = models.CharField(max_length=100, blank=True, null=True)
    # village = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'damage_crop'


class MahaVillage(models.Model):
    district = models.CharField(max_length=100)
    tehsil = models.CharField(max_length=100)
    village = models.CharField(max_length=100)

    class Meta:
        managed = False  #   important: don't let Django try to create or alter it
        db_table = 'maha_villages_11july22'
        ordering = ['district', 'tehsil', 'village']

    def __str__(self):
        return f"{self.village} ({self.tehsil}, {self.district})"


# For uplaod video and photo 
# def validate_file_type_and_size(value):
#     max_size_mb = 20
#     if value.size > max_size_mb * 1024 * 1024:
#         raise ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

#     # Determine content type safely
#     content_type = getattr(value.file, "content_type", "").lower()

#     allowed_images = ["image/jpeg", "image/png"]
#     allowed_videos = ["video/mp4", "video/quicktime", "video/webm"]
#     allowed_audio  = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/wave", "audio/ogg", "audio/webm"]

#     if content_type in allowed_images:
#         return
#     elif content_type in allowed_videos:
#         return
#     elif content_type in allowed_audio:
#         return
#     else:
#         raise ValidationError(
#             "Unsupported file format. Allowed:\n"
#             "Images: JPG, PNG\n"
#             "Videos: MP4, MOV, WEBM\n"
#             "Audio: MP3, WAV, OGG, WEBM"
#         )
def validate_file_type_and_size(allowed_types, max_size_mb=20):
    def validator(value):
        if value.size > max_size_mb * 1024 * 1024:
            raise ValidationError(
                f"File too large! Maximum allowed size is {max_size_mb} MB."
            )

        content_type = getattr(value.file, "content_type", "").lower()

        if content_type not in allowed_types:
            raise ValidationError(
                f"Unsupported file format. Allowed: {', '.join(allowed_types)}"
            )

    return validator


# def validate_file_type_and_size(value):
#     max_size_mb = 20
#     allowed_types = ['image/jpeg', 'image/png', 'video/mp4', 'video/quicktime']

#     if value.size > max_size_mb * 1024 * 1024:
#         raise ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

#     # SAFELY read content_type
#     content_type = getattr(value.file, "content_type", None)

#     if not content_type or content_type not in allowed_types:
#         raise ValidationError("Unsupported file format. Allowed: JPG, PNG, MP4, MOV.")

    
# def validate_file_type_and_size(value):
#     max_size_mb = 20
#     allowed_types = ['image/jpeg', 'image/png', 'video/mp4', 'video/quicktime']

#     if value.size > max_size_mb * 1024 * 1024:
#         raise ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")
#     allowed_types = [
#         "image/jpeg",
#         "image/png",
#         "video/mp4",
#         "video/quicktime",
#         "audio/wav",
#           "audio/x-wav",
#           "audio/wave",
#           "audio/ogg",
#           "audio/mpeg",
#           "audio/mp3",
#           "audio/webm"
#     ]
#     if value.file.content_type not in allowed_types:
#         raise ValidationError("Unsupported file format. Allowed: JPG, PNG, MP4, MOV.")


class DtProduce(models.Model):
    username = models.ForeignKey(
        'User1',
        to_field='username',  #   Tell Django to use username instead of id
        on_delete=models.CASCADE,
        db_column='username_id'
    )
    sale_commodity = models.CharField(max_length=100)
    variety_name = models.CharField(max_length=100)
    # method = models.CharField(max_length=20, choices=[('organic', 'Organic'), ('inorganic', 'Inorganic')], blank=True,   # allows form submissions to leave it empty
    # null=True )    # allows NULL value in database)
    # level_of_produce = models.CharField(max_length=50, choices=[
    #     ('selling surplus', 'Selling Surplus'),
    #     ('selling surplus with value addition', 'Selling Surplus with Value Addition')
    # ])
    # sowing_date = models.DateField(blank=True, null=True)
    # harvest_date = models.DateField(blank=True, null=True)
    quantity_for_sale = models.FloatField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=[
        ('Kg', 'Kg'), ('250 gm', '250 gm'), ('bundle', 'Bundle'),
        ('piece', 'Piece'), ('dozen', 'Dozen')
    ])
    # produce_expense = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    # profit_expectation = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    photo_or_video = models.FileField(
        upload_to='produce_media/',
        blank=True,
        null=True,
        # validators=[validate_file_type_and_size([
        # validators=[FileTypeAndSizeValidator([
        #     "image/jpeg", "image/png",
        #     "video/mp4", "video/quicktime", "video/webm"
        # ])]
        validators=[validate_media_file] 
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    created_at = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)  # Multi language text
    description_voice = models.FileField(
        upload_to='produce_voice/',
        blank=True,
        null=True,
        # validators=[validate_file_type_and_size([
        # validators=[FileTypeAndSizeValidator([
        #     "audio/mpeg", "audio/mp3", "audio/wav",
        #     "audio/x-wav", "audio/wave",
        #     "audio/ogg", "audio/webm"
        # ])
    # ]
    validators=[validate_audio_file]
    )  # Voice input file (audio)

    def clean(self):
        """
        Ensure that if a photo/video is uploaded,
        both latitude and longitude are provided and valid.
        """
        if self.photo_or_video:
            if not self.latitude or not self.longitude:
                raise ValidationError("Latitude and Longitude are required when uploading media.")

    def save(self, *args, **kwargs):
        # 🟢 Skip full_clean() — form already validates input
        super().save(*args, **kwargs)

        # 🟡 Optional image compression (only for images)
        if self.photo_or_video:
            file_path = self.photo_or_video.path
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png']:
                try:
                    img = Image.open(file_path)
                    max_width = 1200
                    if img.width > max_width:
                        w_percent = max_width / float(img.width)
                        h_size = int(float(img.height) * w_percent)
                        img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
                    img.save(file_path, optimize=True, quality=70)
                except Exception as e:
                    print(f"⚠️ Image compression error: {e}")

    class Meta:
        db_table = 'dt_produce'
        
class MobileOTP(models.Model):
    mobile = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)  
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)
    class Meta:
        db_table = "syncapp_mobileotp"