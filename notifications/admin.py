from django.contrib import admin

from .models import *

class NotifyAdmin(admin.ModelAdmin):
    list_display = ('template', 'users', 'status')
    list_filter = ('users__email', 'users')
    search_filter = ('users__email',)


admin.site.register(EmailNotifications, NotifyAdmin)
admin.site.register(EmailTemplates)
