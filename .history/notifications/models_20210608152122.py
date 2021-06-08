import jsonfield
from django.db import models

from user.models import LmsUser
from lms.constants import CHOICE_FIELDS


class EmailTemplates(models.Model):
    subject = models.CharField(max_length=50)
    body = models.TextField(max_length=1000)
    purpose = models.CharField(max_length=100)
    model = models.CharField(max_length=15, choices=CHOICE_FIELDS)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)

    def __str__(self):
        return self.subject


class EmailNotifications(models.Model):
    template = models.ForeignKey(EmailTemplates, on_delete=models.CASCADE)
    users = models.ForeignKey(LmsUser, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    required_data = jsonfield.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)

    def __str__(self):
        return self.template.subject
