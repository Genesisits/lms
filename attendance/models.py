from django.db import models
from django.conf import settings

from businessGroup.models import BaseClass, Batch
from lms.constants import ATTENDANCE_CHOICES


class Attendance(BaseClass):
    attendances = models.CharField(max_length=8, choices=ATTENDANCE_CHOICES, blank=True)
    trainees = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE, related_name="attend"
    )
    batches = models.ForeignKey(
        Batch, blank=True, null=True, on_delete=models.CASCADE, related_name="batch_attend"
    )
    schedule = models.DateField()

    def __str__(self):
        return self.trainees.first_name
