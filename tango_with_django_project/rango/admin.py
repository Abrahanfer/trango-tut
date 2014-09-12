from django.contrib import admin
from rango.models import Category, Page


class PageAdmin(admin.ModelAdmin):
    #fieldsets=[
     #   ('Title', {'fields': ['title']}),
      #  ('Category', {'fields': ['category']}),
       # ('Url', {'fields': ['url']})
    #]

    list_display = ('title', 'category_name', 'url')

# Register your models here.
admin.site.register(Category)
admin.site.register(Page, PageAdmin)
