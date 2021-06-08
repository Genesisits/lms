import datetime
import logging

from django.core.management.base import BaseCommand

from assessment.models import BatchAssessment
from businessGroup.views import notify_email

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "assessment not answered notification"

    def handle(self, *args, **kwargs):
        assessments = BatchAssessment.objects.filter(active=True)
        for assessment in assessments:
            if assessment.end_at - datetime.timedelta(days=1) == datetime.date.today():
                notify_email(module="ASSESSMENT", purpose="deadline", id=assessment.id,
                             required_for={"assessment": assessment.assmt.assessment_name,
                                           "batch": assessment.batches.name, "date": assessment.end_at})

            if assessment.end_at == datetime.date.today():
                notify_email(module="ASSESSMENT", purpose="not_submitted", id=assessment.id,
                             required_for={"assessment": assessment.assmt.assessment_name,
                                           "batch": assessment.batches.name, "date": assessment.end_at})
            logger.info("assessment submission date")
        logger.error("assessment submission")
