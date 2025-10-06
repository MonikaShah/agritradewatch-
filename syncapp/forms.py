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
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",   # store commodity name in farmer.commodity
        empty_label="Select Commodity"
    )

    class Meta:
        model = Farmer1
        fields = ["commodity", "sellingprice", "quantitysold", "unit", "date", "image"]
        widgets = {
            'commodity': forms.TextInput(attrs={'class': 'form-control'}),
            'quantitysold': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
