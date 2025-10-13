from django import forms
from .models import Consumer1, Farmer1, Commodity

class ConsumerForm(forms.ModelForm):
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",
        empty_label="Select Commodity",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Consumer1
        fields = ["commodity", "buyingprice", "quantitybought", "unit", "image", "date"]
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'buyingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter buying price'}),
            'quantitybought': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit (e.g., Kg, litre)'}),
            'date': forms.TextInput(attrs={
                'class': 'form-control datetimepicker',
                'placeholder': 'Select date & time',
                'autocomplete': 'off'
            }),
        }


class FarmerForm(forms.ModelForm):
    UNIT_CHOICES = [
        ('2.5 Kg', '2.5 Kg'),
        ('Kg', 'Kg'),
        ('Bundle', 'Bundle'),
        ('Piece', 'Piece'),
        ('Dozen', 'Dozen'),
    ]

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
        fields = ["commodity", "sellingprice", "quantitysold", "unit", "date", "image"]
        widgets = {
            'sellingprice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter selling price'}),
            'quantitysold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'date': forms.TextInput(attrs={
                'class': 'form-control datetimepicker',
                'placeholder': 'Select date & time',
                'autocomplete': 'off'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
