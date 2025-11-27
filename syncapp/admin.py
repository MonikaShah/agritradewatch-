from django.contrib import admin
from .models import Commodity,Consumer1,Farmer1,User1,WebData,Page,APMC_Market_Prices,APMC_Master,DtProduce,DamageCrop  # replace with your actual models
from django.utils.html import format_html
from django.db.models import F  # Make sure to import F

# class MarketPricesAdmin(admin.ModelAdmin):
#     list_display = ('arrival_date', 'market', 'commodity', 'variety', 'min_price','max_price','modal_price')  # columns to show
#     list_filter = ('market', 'commodity', 'variety', 'arrival_date')            # filters in sidebar
#     search_fields = ('market', 'commodity', 'variety')                          # search bar

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'image_tag')
    readonly_fields = ('image_tag',)  # show image preview in the edit page

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

class Users1Admin(admin.ModelAdmin):
    list_display = ('username', 'name', 'mobile','profile_pic')
    list_filter = ('username', 'job', 'is_staff')                          # search bar

class Consumers1Admin(admin.ModelAdmin):
    list_display = ('date', 'commodity','user_name', 'userid')
    list_filter = ['date','commodity']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Order by date descending, NULLs last
        return qs.order_by(F('date').desc(nulls_last=True))

    def user_name(self, obj):
        try:
            user = User1.objects.get(id=obj.userid)
            return user.name
        except User1.DoesNotExist:
            return '-'

    user_name.short_description = 'Username'

class Farmer1Admin(admin.ModelAdmin):
    list_display = ('commodity', 'date', 'sellingprice','user_name','userid')
    list_filter = ['date']
    ordering = ['-date']

    def user_name(self, obj):
        try:
            user = User1.objects.get(id=obj.userid)
            return user.username
        except User1.DoesNotExist:
            return '-'

    user_name.short_description = 'Username'


class WebdataAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'source', 'date', 'apmc')
    list_filter = ['date']

class DrProduceAdmin(admin.ModelAdmin):
    list_display = ('sale_commodity', 'username_id','variety_name','quantity_for_sale', 'created_at','photo_or_video')
    list_filter = ['created_at']

class CommodityAdmin(admin.ModelAdmin):
    list_display = ('name','alias_marathi','type')
    ordering = ['name']

# Register models
# admin.site.register(MarketPrices, MarketPricesAdmin)
admin.site.register(Consumer1,Consumers1Admin)
admin.site.register(Farmer1,Farmer1Admin)
admin.site.register(User1,Users1Admin)
admin.site.register(WebData,WebdataAdmin)
admin.site.register(Page,PageAdmin)
admin.site.register(Commodity,CommodityAdmin)
admin.site.register(APMC_Master)
admin.site.register(DamageCrop)
admin.site.register(DtProduce,DrProduceAdmin)


# Register your models here.
