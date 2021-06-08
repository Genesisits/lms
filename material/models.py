from django.db import models
from django.conf import settings

from assessment.models import BatchAssessment
from businessGroup.models import Batch, Module, BaseClass
from .validations import validate_file_extension
from lms.constants import VERIFICATION_STATUS


class Material(BaseClass):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=True, on_delete=models.CASCADE, related_name='materialuser')
    as_batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True)
    as_module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(validators=[validate_file_extension], blank=True, null=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    file_status = models.CharField(max_length=15, choices=VERIFICATION_STATUS, default="APPROVED")

    def __str__(self):
        return self.as_batch.name


class FieldStudyObservation(BaseClass):
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE, related_name='obs_trainer')
    batch = models.ManyToManyField(Batch, related_name='field_study')
    trainee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.CASCADE, related_name='obs_trainee')
    lab_name = models.CharField(max_length=150)
    file = models.FileField(upload_to="media/", blank=False, null=False)
    score = models.DecimalField(max_digits=5, decimal_places=2, default='0')
    assessment_is = models.ForeignKey(BatchAssessment, related_name='field',
                                      on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.trainee.first_name
