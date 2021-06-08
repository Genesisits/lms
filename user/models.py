from django.db import models
from django.contrib.auth.models import AbstractUser

from businessGroup.models import Module, Batch
from .validations import validate_image_extension
from lms.constants import GENDER_CHOICES


class LmsUser(AbstractUser):
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    mobile_number = models.CharField(max_length=15)
    location = models.CharField(max_length=100, null=True, blank=True)
    date_of_join = models.DateField(null=True, blank=True)
    image = models.FileField(validators=[validate_image_extension], null=True, blank=True)
    is_course_trainer = models.BooleanField(default=False)
    is_sfe_trainer = models.BooleanField(default=False)
    is_trainee = models.BooleanField(default=False)
    is_country_sales_manager = models.BooleanField(default=False)
    is_training_head = models.BooleanField(default=False)
    designation = models.CharField(max_length=100, null=True, blank=True)
    escalation_status = models.BooleanField(default=False)


class QuestionFeed(models.Model):
    question_text = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)

    def __str__(self):
        return self.question_text


class AnswerFeed(models.Model):
    module = models.ForeignKey(Module, null=True, on_delete=models.CASCADE, related_name='module_feed')
    batch = models.ForeignKey(Batch, null=True, on_delete=models.CASCADE, related_name='batch_feed')
    trainer = models.ForeignKey(LmsUser, blank=True, null=True, on_delete=models.CASCADE, related_name='trainer_feed')
    trainee = models.ForeignKey(LmsUser, blank=True, null=True, on_delete=models.CASCADE, related_name='trainee_feed')
    question = models.ForeignKey(QuestionFeed, null=True, blank=True, related_name='questions',
                                 on_delete=models.CASCADE)
    feedback_answers = models.CharField(max_length=150, null=True, blank=True)
    comment = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null= True)

    def __str__(self):
        return self.trainer.first_name
