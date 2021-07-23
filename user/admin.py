from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import *


class LmsAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'mobile_number', 'gender',
                                         'location', 'designation')}),
        (_('Permissions'), {'fields': ('is_active', )}),
        (_("Role"), {'fields': ('is_superuser', 'is_training_head', 'is_course_trainer',
                                'is_sfe_trainer', 'is_trainee', 'is_country_sales_manager',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')}),)

    list_display = ('username', 'email', 'first_name', 'last_name', 'mobile_number',
                    'gender', 'location', 'is_superuser', 'is_training_head',
                    'is_course_trainer', 'is_sfe_trainer', 'is_trainee', 'designation')
    list_filter = ('is_active', 'is_trainee', 'is_course_trainer', 'is_sfe_trainer',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile_number', 'gender', 'location',
                     'designation')
    ordering = ('username',)


admin.site.register(LmsUser, LmsAdmin)
admin.site.register(QuestionFeed)
admin.site.register(AnswerFeed)
# admin.site.register(Effectiveness)
