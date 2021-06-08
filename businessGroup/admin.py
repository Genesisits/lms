from django.contrib import admin

from .models import BusinessGroup, Level, Module, Batch

admin.site.register(Batch)
admin.site.register(BusinessGroup)
admin.site.register(Level)
admin.site.register(Module)
