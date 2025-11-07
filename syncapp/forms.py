from django import forms
from .models import Consumer1, Farmer1, Commodity, User1,  MahaVillage, DamageCrop
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