from django import forms
from .models import Consumer1, Farmer1, Commodity, User1
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