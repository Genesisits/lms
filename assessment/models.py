import jsonfield
from django.db import models
from django.conf import settings

from businessGroup.models import BaseClass, Module, Batch
from lms.constants import TYPE_CHOICES, VERIFICATION_STATUS, VERIFY_INIT, ANSWER_CHOICES, ANSWER_INACTIVE


class Assessment(BaseClass):
    assessment_name = models.CharField(max_length=20, null=True, blank=False, unique=True)
    as_module = models.ForeignKey(Module, null=True, on_delete=models.CASCADE)
    as_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    def __str__(self):
        return self.assessment_name


class BatchAssessment(BaseClass):
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.CASCADE, related_name='trassessment'
    )
    batches = models.ForeignKey(Batch, null=True, on_delete=models.CASCADE, related_name="batch")
    assmt = models.ForeignKey(
        Assessment, blank=True, null=True,
        on_delete=models.CASCADE, related_name='assessment'
    )
    assessment_data = jsonfield.JSONField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=VERIFICATION_STATUS, default="IN PROGRESS")
    duration = models.DurationField(null=True, blank=True)
    scheduled_at = models.DateField(null=True, blank=True)
    end_at = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.assmt.assessment_name


class Answer(BaseClass):
    trainee = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                on_delete=models.CASCADE, related_name='answer')
    assessments = models.ForeignKey(BatchAssessment, blank=True, null=True,
                                    on_delete=models.CASCADE, related_name='batch_assessment')
    answer_data = jsonfield.JSONField(null=True, blank=True)
    submit = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=ANSWER_CHOICES, default=ANSWER_INACTIVE
    )
    attendance_update = models.BooleanField(default=True)
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2, default='0', null=True, blank=True
    )

    def __str__(self):
        return self.trainee.first_name


class MultipartData(models.Model):
    file = models.FileField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)


class CpcEvaluate(BaseClass):
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                on_delete=models.CASCADE, related_name='cpc_trainer')
    cpbatch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='cpc_batch')
    trainee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.CASCADE, related_name='cpc_trainee')
    no_of_cpcs_attended = models.CharField(max_length=150)
    score = models.DecimalField(max_digits=5, decimal_places=2, default='0')
    assessment_is = models.ForeignKey(BatchAssessment, related_name='cpc_assessment',
                                      on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.trainee.first_name
