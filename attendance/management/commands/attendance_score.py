import logging

from django.core.management.base import BaseCommand

from assessment.models import Answer, BatchAssessment
from attendance.models import *
from attendance.views import attendance_calculate
from user.models import LmsUser
from businessGroup.views import notify_email
from assessment.views import scores_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "full attendance for who completes assessment"

    def handle(self, *args, **kwargs):

        attend_assess = {"spine and biologics": 7, "surgical synergy": 7,
                        "trauma": 5, "neurosurgery": 7,
                        "neurovascular": 7, "neuromodulation": 5, "ent": 7}

        batches = Batch.objects.filter(is_active=True)

        for bat in batches:
            batch = Batch.objects.filter(id=bat.id)
            trainees = batch.values_list("trainee", flat=True)
            for trainee in trainees:
                user = LmsUser.objects.get(id=trainee)
                percent = attendance_calculate(trainee)
                assess = BatchAssessment.objects.get(assmt__as_type="attendance",
                                                     batches=bat.id).id if BatchAssessment.objects.filter(
                    assmt__as_type="attendance", batches=bat.id).exists() else None
                assessments = Answer.objects.filter(trainee=trainee, assessments__batches=bat.id)
                if len(assessments) == attend_assess[bat.business_group.name.lower()]:
                    Answer.objects.create(trainee=LmsUser.objects.get(id=trainee),
                                          assessments=BatchAssessment.objects.get(id=assess),
                                          status='reviewed', total_score=percent, submit=True)

                    if float(percent) < 100:
                        notify_email(module="ASSESSMENT", purpose="required_cutoff",
                                     id=Answer.objects.get(trainee=trainee, assessments=assess).id,
                                     required_for={"batch": bat.name, "user": user.first_name + " " + user.last_name})

                if Answer.objects.filter(trainee=trainee, assessments__batches=bat.id,
                                         assessments__assmt__assessment_name="A33"):
                    scores = scores_list(trainee, bat.business_group, bat.id)
                    test = [tr["trainee_status"] for tr in scores if "trainee_status" in tr]
                    if test[0] == "NOT CLEARED":
                        notify_email(module="ASSESSMENT", purpose="required_cutoff",
                                     id=Answer.objects.get(trainee=trainee, assessments__batches=bat.id,
                                                           assessments=assess).id,
                                     required_for={"batch": bat.name, "user": user.first_name + " " + user.last_name})
                logger.info("attendance score calculated")
        logger.error("attendance score")
