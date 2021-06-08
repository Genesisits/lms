from datetime import date
from django.core.management.base import BaseCommand

from assessment.models import BatchAssessment


class Command(BaseCommand):
    help = "Assessments List"

    def handle(self, *args, **options):
        assessments = BatchAssessment.objects.filter(batches__trainee=51,
                                                status="APPROVED", end_at__gte=date.today())
        for assessment in assessments:
            print(assessment.id, assessment.assmt.assessment_name, assessment.batches.name)
        return "success"