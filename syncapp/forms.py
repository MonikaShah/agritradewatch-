from django import forms
from .models import Consumer1, Farmer1, Commodity, User1,  MahaVillage, DamageCrop,DtProduce
from django.contrib.auth.forms import PasswordResetForm

UNIT_CHOICES = [
        ('2.5 Kg', '2.5 Kg'),
        ('Kg', 'Kg'),
        ('Bundle', 'Bundle'),
        ('Piece', 'Piece'),
        ('Dozen', 'Dozen'),
    ]
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
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'buyingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter buying price'}),
            'quantitybought': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit (e.g., Kg, litre)'}),
            # 'date': forms.TextInput(attrs={
            #     'class': 'form-control datetimepicker',
            #     'placeholder': 'Select date & time',
            #     'autocomplete': 'off'
            # }),
        }


class FarmerForm(forms.ModelForm):
    

    # Define commodity as before
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",
        empty_label="Select Commodity",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Define unit as a ChoiceField (not in widgets)
    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Farmer1
        fields = ["commodity", "sellingprice", "quantitysold", "unit",  "image"]
        widgets = {
            'sellingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter selling price'}),
            'quantitysold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            # 'date': forms.TextInput(attrs={
            #     'class': 'form-control datetimepicker',
            #     'placeholder': 'Select date & time',
            #     'autocomplete': 'off'
            # }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

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
    
# class ThelaForm(forms.ModelForm):
#     district = forms.ChoiceField(choices=[], required=True)
#     tehsil = forms.ChoiceField(choices=[], required=True)
#     village = forms.ChoiceField(choices=[], required=True)

#     class Meta:
#         model = Thela
#         fields = [
#             'commodity', 'damage', 'unit', 'damage_date', 'report_date',
#             'remarks'
#         ]
#         widgets = {
#             'commodity': forms.TextInput(attrs={'class': 'form-control'}),
#             'damage': forms.NumberInput(attrs={'class': 'form-control'}),
#             'unit': forms.TextInput(attrs={'class': 'form-control'}),
#             'damage_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
#             'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#         }   'place_damage':
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)

#     #     # Populate district dropdown
#     #     districts = MahaVillage.objects.values_list('district', flat=True).distinct().order_by('district')
#     #     self.fields['district'].choices = [('', 'Select District')] + [(d, d) for d in districts]

#     #     # If district is posted, populate tehsils
#     #     if 'district' in self.data and self.data.get('district'):
#     #         district = self.data.get('district')
#     #         tehsils = MahaVillage.objects.filter(district=district).values_list('tehsil', flat=True).distinct().order_by('tehsil')
#     #         self.fields['tehsil'].choices = [('', 'Select Tehsil')] + [(t, t) for t in tehsils]

#     #     # If tehsil is posted, populate villages
#     #     if 'tehsil' in self.data and self.data.get('tehsil'):
#     #         tehsil = self.data.get('tehsil')
#     #         villages = MahaVillage.objects.filter(tehsil=tehsil).values_list('village', flat=True).distinct().order_by('village')
#     #         self.fields['village'].choices = [('', 'Select Village')] + [(v, v) for v in villages]


class DamageForm(forms.ModelForm):
    class Meta:
        model = DamageCrop
        fields = [
            'commodity',
            'damage',
            'unit',
            'place_damage',   # ✅ new dropdown
            'damage_date',
            'report_date',
            'remarks',
            'photo',          # ✅ new image upload field
        ]

        widgets = {
            'commodity': forms.TextInput(attrs={'class': 'form-control'}),
            'damage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'place_damage': forms.Select(attrs={'class': 'form-select'}),
            'damage_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# class DtLoginForm(forms.Form):
#     username = forms.CharField(
#         label="Username",
#         widget=forms.TextInput(attrs={
#             "class": "form-control",
#             "placeholder": "Enter your username"
#         })
#     )
#     password = forms.CharField(
#         label="Password",
#         widget=forms.PasswordInput(attrs={
#             "class": "form-control",
#             "placeholder": "Enter your password"
#         })
#     )

# class DtUserForm(forms.ModelForm):
#     class Meta:
#         model = DtUser
#         fields = ['name', 'username', 'email', 'mobile', 'password', 'latitude', 'longitude', 'job']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
#             'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
#             'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
#             'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
#             'job': forms.Select(attrs={'class': 'form-select'}),
#             'latitude': forms.HiddenInput(),
#             'longitude': forms.HiddenInput(),
#         }

#     def clean_password(self):
#         password = self.cleaned_data.get('password')
#         if len(password) < 6:
#             raise forms.ValidationError("Password must be at least 6 characters long.")
#         return password
    

# class DtProduceForm(forms.ModelForm):
#     class Meta:
#         model = DtProduce
#         fields = [
#             'sale_commodity', 'variety_name', 'method',
#             'level_of_produce', 'sowing_date', 'harvest_date',
#             'quantity_for_sale', 'cost', 'unit', 'produce_expense',
#             'profit_expectation', 'photo_or_video', 'latitude', 'longitude'
#         ]
#         widgets = {
#             'username': forms.Select(attrs={'class': 'form-select'}),
#             'sale_commodity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter commodity name'}),
#             'variety_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter variety name'}),
#             'method': forms.Select(attrs={'class': 'form-select'}),
#             'level_of_produce': forms.Select(attrs={'class': 'form-select'}),
#             'sowing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'harvest_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'quantity_for_sale': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
#             'cost': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter cost per unit'}),
#             'unit': forms.Select(attrs={'class': 'form-select'}),
#             'produce_expense': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total expense'}),
#             'profit_expectation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected profit'}),
#             'photo_or_video': forms.ClearableFileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.jpg,.jpeg,.png,.mp4,.mov'
#             }),
#             'latitude': forms.HiddenInput(),
#             'longitude': forms.HiddenInput(),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         file = cleaned_data.get('photo_or_video')
#         lat = cleaned_data.get('latitude')
#         lon = cleaned_data.get('longitude')

#         # ✅ Location required only if media uploaded
#         if file:
#             if not lat or not lon:
#                 raise forms.ValidationError("Please enable location before uploading your photo or video.")

#             # ✅ Restrict file size
#             max_size_mb = 20
#             if file.size > max_size_mb * 1024 * 1024:
#                 raise forms.ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

#             # ✅ Restrict allowed formats
#             allowed_types = ['image/jpeg', 'image/png', 'video/mp4', 'video/quicktime']
#             if file.content_type not in allowed_types:
#                 raise forms.ValidationError("Unsupported file format. Allowed: JPG, PNG, MP4, MOV")

#         return cleaned_data

class DtProduceForm(forms.ModelForm):
    NEW_COMMODITY_VALUE = "add_new"
    # Add a new field for custom commodity
    new_commodity = forms.CharField(
        max_length=100,
        required=False,
        label="Add New Commodity",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new commodity name'})
    )
    description = forms.CharField(
        required=False,
        label="Description (English / Marathi / Hindi)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your produce...',
            'rows': 3
        })
    )

    description_voice = forms.FileField(
        required=False,
        label="Voice Description (optional)",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.mp3,.wav,.ogg'  # Only audio
        })
    )
    class Meta:
        model = DtProduce
        fields = [
            'sale_commodity', 'variety_name', 
            'quantity_for_sale', 'cost', 'unit', 'photo_or_video', 'latitude', 'longitude',
             'description','description_voice'
        ]

        labels = {
            'sale_commodity': 'Commodity',
            'variety_name': 'Variety Name',
            # 'method': 'Method of Production',
            # 'level_of_produce': 'Production Level',
            # 'sowing_date': 'Sowing Date',
            # 'harvest_date': 'Harvest',
            'quantity_for_sale': 'Quantity for Sale',
            'cost': 'Cost per Unit',
            'unit': 'Unit',
            # 'produce_expense': 'Total Expense',
            # 'profit_expectation': 'Expected Profit',
            'photo_or_video': 'Photo / Video (optional)',
        }

        widgets = {
            'sale_commodity': forms.Select(attrs={'class': 'form-select'}),
            'variety_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter variety name'}),
            # 'method': forms.Select(attrs={'class': 'form-select'}),
            # 'level_of_produce': forms.Select(attrs={'class': 'form-select'}),
            # 'sowing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # 'harvest_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantity_for_sale': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter cost per unit'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            # 'produce_expense': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total expense'}),
            # 'profit_expectation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected profit'}),
            'photo_or_video': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.mp4,.mov'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        widget=forms.ClearableFileInput(attrs={'accept': 'audio/*'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Add predefined commodities + "Add new" option
        commodity_choices = [
            ('', 'Select a commodity'),
            ('garlic', 'Garlic'),
            ('wheat', 'Wheat'),
            ('sugarcane', 'Sugarcane'),
            ('maize', 'Maize'),
            ('ghee', 'Ghee'),
            ('honey', 'Honey'),
            (self.NEW_COMMODITY_VALUE, '➕ Add New Commodity'),
        ]
        self.fields['sale_commodity'].widget.choices = commodity_choices

        # self.fields['sale_commodity'].widget = forms.Select(
        #     choices=commodity_choices,
        #     attrs={'class': 'form-select', 'id': 'id_sale_commodity'}
        # )

        # self.fields['sowing_date'].required = False
        # self.fields['harvest_date'].required = False
        # self.fields['produce_expense'].required = False
        # self.fields['profit_expectation'].required = False


        # ✅ Mark required fields visually with red asterisk
        for field_name, field in self.fields.items():
            if field.required:
                field.label = forms.utils.mark_safe(f"{field.label} <span style='color:red;'>*</span>")

    # def clean(self):
    #     cleaned_data = super().clean()
    #     sale = cleaned_data.get("sale_commodity")
    #     new_sale = cleaned_data.get("new_commodity")

    #     # If "Add New Commodity" selected, require new_commodity
    #     if sale == self.NEW_COMMODITY_VALUE:
    #         if not new_sale:
    #             raise forms.ValidationError("Please enter a new commodity name.")
    #         cleaned_data["sale_commodity"] = new_sale  # replace with new commodity

    #     file = cleaned_data.get('photo_or_video')
    #     lat = cleaned_data.get('latitude')
    #     lon = cleaned_data.get('longitude')
    #     voice = cleaned_data.get('description_voice')

    #     # ✅ Location required only if media uploaded
    #     if file:
    #         if not lat or not lon:
    #             raise forms.ValidationError("Please enable location before uploading your photo or video.")

    #         # ✅ Restrict file size
    #         max_size_mb = 20
    #         if file.size > max_size_mb * 1024 * 1024:
    #             raise forms.ValidationError(f"File too large! Maximum allowed size is {max_size_mb} MB.")

    #         # ✅ Restrict allowed formats
    #         allowed_types = ['image/jpeg', 'image/png', 'video/mp4', 'video/quicktime']
    #         if file.content_type not in allowed_types:
    #             raise forms.ValidationError("Unsupported file format. Allowed: JPG, PNG, MP4, MOV")

    #         # Optional voice file size/type check
    #     if voice:
    #         max_size_mb = 20
    #         if voice.size > max_size_mb * 1024 * 1024:
    #             raise forms.ValidationError(f"Voice file too large! Max {max_size_mb} MB allowed.")

    #     allowed_audio = ['audio/mpeg', 'audio/wav', 'audio/ogg']
    #     if voice.content_type not in allowed_audio:
    #         raise forms.ValidationError("Unsupported audio format. Allowed: MP3, WAV, OGG")

    #     return cleaned_data
    def clean(self):
        cleaned_data = super().clean()

        # Handle Add New commodity
        sale = cleaned_data.get("sale_commodity")
        new_sale = cleaned_data.get("new_commodity")
        if sale == self.NEW_COMMODITY_VALUE:
            if not new_sale:
                raise forms.ValidationError("Please enter a new commodity name.")
            cleaned_data["sale_commodity"] = new_sale

        file = cleaned_data.get("photo_or_video")
        voice = cleaned_data.get("description_voice")
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")

        #Validate media separately
        if file:
            if not lat or not lon:
                raise forms.ValidationError("Please select location before uploading media.")
            max_size_mb = 20
            if file.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"File too large! Max allowed size is {max_size_mb} MB.")
            allowed_media = ["image/jpeg", "image/png", "video/mp4", "video/quicktime"]
            if file.content_type not in allowed_media:
                raise forms.ValidationError("Unsupported file format. Allowed: JPG, PNG, MP4, MOV.")

        # Accept correct WAV mime variants + MP3/OGG
        if voice:
            max_size_mb = 20
            if voice.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Voice file too large! Max allowed size is {max_size_mb} MB.")

            allowed_audio_types = [
                "audio/wav",
                "audio/x-wav",    
                "audio/wave",
                "audio/x-pn-wav", 
                "audio/ogg",
                "audio/mpeg",
                "audio/mp3",
            ]

            if voice.content_type not in allowed_audio_types:
                raise forms.ValidationError("Unsupported audio format. Allowed: MP3, WAV, OGG.")

        return cleaned_data
