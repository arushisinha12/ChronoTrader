

# Register your models here.
from django.contrib import admin
from .models import Player, Inventory

# Register your models here so they appear in the admin site.
admin.site.register(Player)
admin.site.register(Inventory)