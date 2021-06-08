import datetime
import logging

from django.core.management.base import BaseCommand

from assessment.models import BatchAssessment
from businessGroup.models import Batch
from businessGroup.views import notify_email

from lms.constants import (
    ASSESSMENT_LIST
)

logger = logging.getLogger(__name__)


def assessment_compare(assessment, name):
    try:
        return assessment.get(assmt__assessment_name=name)
    except Exception as e:
        print("Exception while creating assessment", e)
        return None


def assessment_add(batch_date, a):
    try:
        return batch_date + datetime.timedelta(weeks=a)
    except Exception as e:
        print("Exception while fetching batch date", e)
        return None


def active_assessment(bgs, a11=None, a12=None, a13=None, a2=None, a33=None, a34=None, a31=None, a32=None):
    batch = Batch.objects.all()
    l2 = []
    d = {"a": a11, "b": a12, "c": a13, "d": a2, "e": a33, "f": a34, "g": a31, "h": a32}
    for batch in batch.filter(business_group__name=bgs):
        batch_date = batch.start_date
        assessment = BatchAssessment.objects.filter(batches=batch)

        if assessment.exists():
            l2 = [assessment_compare(assessment, x) for x in ASSESSMENT_LIST]
            today = datetime.datetime.today().date()
            for x in d.values():
                for y in l2:
                    if assessment_add(batch_date, x) == today:
                        y.active = True
                        y.end_at = today + datetime.timedelta(weeks=1)
                        y.save()
                        notify_email(module="ASSESSMENT", purpose="activate", id=y.id,
                                     required_for={"assessment": y.assmt.assessment_name, "batch": y.batches.name, "date": y.end_at, "type": y.assmt.as_type})
                    break


class Command(BaseCommand):
    help = "activate assessment at required period"

    def handle(self, *args, **kwargs):
        assessments = BatchAssessment.objects.filter(active=False)
        for assessment in assessments:
            if assessment.scheduled_at:
                if datetime.date.today() == assessment.scheduled_at:
                    assessment.active = True
                    assessment.end_at = datetime.date.today() + datetime.timedelta(weeks=1)
                    assessment.save()
                    notify_email(module="ASSESSMENT", purpose="activate", id=assessment.id,
                                 required_for={"assessment": assessment.assmt.assessment_name,
                                               "batch": assessment.batches.name,"date": assessment.end_at,
                                               "assessmenttype": assessment.assmt.as_type})
            else:
                active_assessment('spine and biologics', 4, 8, 9, 9, 23, 14, 23, 23)
                active_assessment('surgical synergy', 4, 8, 9, 9, 23, 14, 23, 23)
                active_assessment('trauma', 2, 3, 0, 8, 11, 11)
                active_assessment('neurosurgery', 8, 8, 0, 8, 23, 18, 17, 17)
                active_assessment('neurovascular', 3, 3, 0, 3, 7, 5, 7, 7)
                active_assessment('neuromodulation', 3, 2, 0, 5, 14, 9)
                active_assessment('ent', 0, 0, 2, 3, 15, 8, 4, 4)
            logger.info("assessment is activated")
        logger.error("assessment activation")
