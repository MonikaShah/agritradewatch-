from django import forms
from .models import Consumer1, Farmer1, Commodity

class ConsumerForm(forms.ModelForm):
    commodity = forms.ModelChoiceField(
        queryset=Commodity.objects.all(),
        to_field_name="name",
        empty_label="Select Commodity"
    )

    class Meta:
        model = Consumer1
        fields = ["commodity", "buyingprice", "quantitybought", "unit", "date"]
        widgets = {
            'commodity': forms.TextInput(attrs={'class': 'form-control'}),
            'quantitybought': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }# exclude = ['id', 'userid']

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
