from django import forms
from .models import Consumer1, Farmer1, Commodity, User1,  MahaVillage, DamageCrop,DtProduce
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

UNIT_CHOICES = [
    ('2.5 Kg', _('2.5 Kg')),
    ('Kg', _('Kg')),
    ('Bundle', _('Bundle')),
    ('Piece', _('Piece')),
    ('Dozen', _('Dozen')),
]
# class ConsumerForm(forms.ModelForm):
#     commodity = forms.ModelChoiceField(
#         queryset=Commodity.objects.all(),
#         to_field_name="name",
#         empty_label="Select Commodity",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     unit = forms.ChoiceField(
#         choices=UNIT_CHOICES,
#         widget=forms.Select(attrs={'class': 'form-select'}),
#         required=True
#     )

#     class Meta:
#         model = Consumer1
#         fields = ["commodity", "buyingprice", "quantitybought", "unit", "image"]
#         widgets = {
#             'latitude': forms.HiddenInput(),
#             'longitude': forms.HiddenInput(),
#             'buyingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter buying price'}),
#             'quantitybought': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
#             'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit (e.g., Kg, litre)'}),
#             # 'date': forms.TextInput(attrs={
#             #     'class': 'form-control datetimepicker',
#             #     'placeholder': 'Select date & time',
#             #     'autocomplete': 'off'
#             # }),
#         }

class ConsumerForm(forms.ModelForm):
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",
        empty_label="Select Commodity",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Consumer1
        fields = ["commodity", "buyingprice", "quantitybought", "unit", "image"]
        exclude = ["latitude", "longitude", "date", "userid", "role"]

        model = Consumer1
        fields = [
            "commodity",
            "buyingprice",
            "quantitybought",
            "unit",
            "image",
            "latitude",
            "longitude",
        ]
# class FarmerForm(forms.ModelForm):
    

#     # Define commodity as before
#     commodity = forms.ModelChoiceField(
#         queryset=Commodity.objects.all(),
#         to_field_name="name",
#         empty_label="Select Commodity",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )

#     # Define unit as a ChoiceField (not in widgets)
#     unit = forms.ChoiceField(
#         choices=UNIT_CHOICES,
#         widget=forms.Select(attrs={'class': 'form-select'}),
#         required=True
#     )

#     class Meta:
#         model = Farmer1
#         fields = ["commodity", "sellingprice", "quantitysold", "unit",  "image"]
#         widgets = {
#             'sellingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter selling price'}),
#             'quantitysold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
#             # 'date': forms.TextInput(attrs={
#             #     'class': 'form-control datetimepicker',
#             #     'placeholder': 'Select date & time',
#             #     'autocomplete': 'off'
#             # }),
#             'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#         }
class FarmerForm(forms.ModelForm):
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",
        empty_label="Select Commodity",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Farmer1
        fields = ["commodity", "sellingprice", "quantitysold", "unit", "image"]
        exclude = ["latitude", "longitude", "date", "userid", "role"]


class MyCustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Override to use your own user model."""
        active_users = User1.objects.filter(email__iexact=email, is_active=True)
        return active_users

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User1.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("No active user found with this email address.")
        return email
    
class DamageForm(forms.ModelForm):
    commodity = forms.ChoiceField(
        choices=[],   # will be filled dynamically
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = DamageCrop
        fields = [
            'commodity',
            'damage',
            'unit',
            'place_damage',
            'damage_date',
            'report_date',
            'remarks',
            'photo',
            'latitude', 'longitude', 'location_accuracy',
        ]

        widgets = {
            # 'commodity': forms.Select(attrs={'class': 'form-select'}),
            'damage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'place_damage': forms.Select(attrs={'class': 'form-select'}),
            'damage_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "location_accuracy": forms.HiddenInput(),
        
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['report_date'].initial = now().date()

        # ✅ Build choices from Commodity table
        commodities = Commodity.objects.order_by('name')

        self.fields['commodity'].choices = [
            (c.name, _(c.name)) for c in commodities
        ]


# class DamageForm(forms.ModelForm):
#     class Meta:
#         model = DamageCrop
#         fields = [
#             'commodity',
#             'damage',
#             'unit',
#             'place_damage',   # ✅ new dropdown
#             'damage_date',
#             'report_date',
#             'remarks',
#             'photo',          # ✅ new image upload field
#             "latitude", "longitude", "location_accuracy",
#         ]
#         labels = {
#             'commodity': _("Commodity"),
#             'damage': _("Damage Quantity"),
#             'unit': _("Unit"),
#             'place_damage': _("Place of Damage"),
#             'damage_date': _("Damage Date"),
#             'report_date': _("Report Date"),
#             'remarks': _("Remarks"),
#             'photo': _("Upload Photo"),
#         }


#         widgets = {
#             'commodity': forms.Select(attrs={'class': 'form-select'}),
#             'damage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
#             'unit': forms.Select(attrs={'class': 'form-select'}),
#             'place_damage': forms.Select(attrs={'class': 'form-select'}),
#             'damage_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            
#             "latitude": forms.HiddenInput(),
#             "longitude": forms.HiddenInput(),
#             "location_accuracy": forms.HiddenInput(),
        
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # default report date
#         self.fields['report_date'].initial = now().date()
#          # ascending commodity list
#             # ✅ Build choices from Commodity table
#         commodities = Commodity.objects.order_by('name')

#         self.fields['commodity'].choices = [
#             (c.name, c.name) for c in commodities
#         ]
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


    
class DtProduceForm(forms.ModelForm):

    NEW_COMMODITY_VALUE = "ADD_NEW"

    class Meta:
        model = DtProduce
        exclude = ["username"]   # <-- IMPORTANT ✔ remove username field
        widgets = {
            "sale_commodity": forms.Select(attrs={"class": "form-control"}),
            "variety_name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity_for_sale": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mark required fields with red asterisk
        for name, field in self.fields.items():
            if field.required:
                field.label = forms.utils.mark_safe(
                    f"{field.label} <span style='color:red;'>*</span>"
                )

    # ---------------- VALIDATION ----------------
    def clean(self):
        cleaned_data = super().clean()

        sale = cleaned_data.get("sale_commodity")
        new_sale = cleaned_data.get("new_commodity", None)

        # --- Add new commodity handling ---
        if sale == self.NEW_COMMODITY_VALUE:
            if not new_sale:
                raise forms.ValidationError("Please enter a new commodity name.")
            cleaned_data["sale_commodity"] = new_sale

        file = cleaned_data.get("photo_or_video")
        voice = cleaned_data.get("description_voice")
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")

        # --- Media validation ---
        if file:
            if not lat or not lon:
                raise forms.ValidationError("Please select location before uploading media.")

            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError("Media file is too large (max 20MB).")

            allowed_media = [
                "image/jpeg", "image/png",
                "video/mp4", "video/quicktime", "video/webm"
            ]
            if file.content_type not in allowed_media:
                raise forms.ValidationError("Allowed: JPG, PNG, MP4, MOV, WEBM.")

        # --- Voice validation ---
        if voice:
            if voice.size > 20 * 1024 * 1024:
                raise forms.ValidationError("Voice file too large (max 20MB).")

            allowed_voice = [
                "audio/wav", "audio/x-wav", "audio/wave",
                "audio/ogg", "audio/mpeg", "audio/mp3",
                "audio/webm"
            ]
            if voice.content_type not in allowed_voice:
                raise forms.ValidationError("Allowed voice: MP3, WAV, OGG.")

        return cleaned_data

class UserProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = User1
        fields = ["profile_pic"]

class SoldForm(forms.ModelForm):
    UNIT_CHOICES = [
        ('kg', 'Kg'),
        ('g', 'Gram'),
        ('quintal', 'Quintal'),
        ('ton', 'Ton'),
        ('litre', 'Litre'),
        ('pcs', 'Pieces'),
    ]

    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    class Meta:
        model = Farmer1
        fields = ['commodity', 'quantitysold', 'unit', 'sellingprice', 'date']
        widgets = {
            'commodity': forms.TextInput(attrs={'readonly': 'readonly'}),
            'date': forms.DateTimeInput(attrs={'readonly': 'readonly', 'type': 'text'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make commodity & date readonly
        self.fields['commodity'].disabled = True
        self.fields['date'].disabled = True

class BoughtForm(forms.ModelForm):
    class Meta:
        model = Consumer1
        fields = ['commodity', 'quantitybought', 'unit', 'buyingprice', 'date']
        widgets = {
            'commodity': forms.TextInput(attrs={'readonly': 'readonly'}),
            'date': forms.DateTimeInput(attrs={'readonly': 'readonly', 'type': 'text'}),
        }