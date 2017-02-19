from django.contrib import admin

# Register your models here.
from .models import City, Place, Place_hours, UserQuery, Category

admin.site.register(City)
admin.site.register(Place)
admin.site.register(Place_hours)
admin.site.register(UserQuery)
admin.site.register(Category)
