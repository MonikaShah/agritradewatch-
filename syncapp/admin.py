from django.contrib import admin
from .models import MarketPrices,Commodity,Consumer1,Farmer1,User1,WebData,Page  # replace with your actual models
from django.utils.html import format_html

class MarketPricesAdmin(admin.ModelAdmin):
    list_display = ('arrival_date', 'market', 'commodity', 'variety', 'min_price','max_price','modal_price')  # columns to show
    list_filter = ('market', 'commodity', 'variety', 'arrival_date')            # filters in sidebar
    search_fields = ('market', 'commodity', 'variety')                          # search bar

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'image_tag')
    readonly_fields = ('image_tag',)  # show image preview in the edit page

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

class Users1Admin(admin.ModelAdmin):
    list_display = ('name', 'mobile')
    list_filter = ('name', 'mobile', 'username')            # filters in sidebar
    search_fields = ('name', 'mobile', 'username')                          # search bar

class Consumers1Admin(admin.ModelAdmin):
    list_display = ('id', 'user_name')  # Show id and name

    def user_name(self, obj):
        try:
            # Look up the name in users1 using the id from consumers1
            user = User1.objects.get(id=obj.userid)
            return user.name
        except User1.DoesNotExist:
            return '-'  # fallback if no match
    user_name.short_description = 'Name'  # Column header

# Register models
admin.site.register(MarketPrices, MarketPricesAdmin)
admin.site.register(Consumer1,Consumers1Admin)
admin.site.register(Farmer1)
admin.site.register(User1,Users1Admin)
admin.site.register(WebData)
admin.site.register(Page,PageAdmin)
admin.site.register(Commodity)


# Register your models here.
