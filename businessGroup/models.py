from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class BaseClass(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class Module(BaseClass):
    name = models.TextField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Level(BaseClass):
    name = models.TextField(max_length=255)
    is_active = models.BooleanField(default=False)
    modules = models.ManyToManyField(Module, blank=True)

    def __str__(self):
        return self.name


class BusinessGroup(BaseClass):
    # levels = models.ManyToManyField(Level, related_name="bg")
    name = models.CharField(max_length=200)
    days = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    training_head = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True,
        limit_choices_to={'is_training_head': True}, related_name='batch_head')
    course_trainer_count = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], null=True, blank=True)
    # sfe_trainer_count = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return self.name


class Batch(BaseClass):
    name = models.CharField(max_length=50)
    business_group = models.ForeignKey(
        BusinessGroup, on_delete=models.CASCADE, null=True, related_name="batch_group")
    course_trainer = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        limit_choices_to={'is_course_trainer': True}, related_name='tbatch_trainers')
    duration = models.DurationField(null=True, blank=True)
    # salesforce_trainer = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL, blank=True,
    #     limit_choices_to={'is_sfe_trainer': True}, related_name='sbatch_trainers')
    trainee = models.ManyToManyField(
        settings.AUTH_USER_MODEL, limit_choices_to={'is_trainee': True}, related_name='batch_trainees')
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    training_status = models.DecimalField(max_digits=4, decimal_places=2, default='0')
    refresher_course = models.BooleanField(default=False)
    batch_notification = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class BatchModuleActivation(models.Model):
    batch = models.ForeignKey(Batch, related_name="batch_module", on_delete=models.CASCADE, null=True)
    # module = models.ForeignKey(Module, related_name="module_active", on_delete=models.CASCADE, null=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.batch.name
