from django.contrib import admin
from .models import MarketPrices,Consumer,Farmer,UserData  # replace with your actual models

class MarketPricesAdmin(admin.ModelAdmin):
    list_display = ('arrival_date', 'market', 'commodity', 'variety', 'min_price','max_price','modal_price')  # columns to show
    list_filter = ('market', 'commodity', 'variety', 'arrival_date')            # filters in sidebar
    search_fields = ('market', 'commodity', 'variety')                          # search bar

# Register models
admin.site.register(MarketPrices, MarketPricesAdmin)
admin.site.register(Consumer)
admin.site.register(Farmer)
admin.site.register(UserData)


# Register your models here.
