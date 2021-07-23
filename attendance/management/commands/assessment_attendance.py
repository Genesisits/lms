import datetime
import logging

from django.core.management.base import BaseCommand

from assessment.models import Answer
from attendance.models import *

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "full attendance for who completes assessment"

    def handle(self, *args, **kwargs):
        answers = Answer.objects.filter(status="reviewed")
        for answer in answers:
            if answer.submit is True:
                as_today = datetime.date.today()
                start = answer.assessments.batches.start_date
                trainee = answer.trainee
                if not Attendance.objects.filter(trainees=trainee, batches=answer.assessments.batches).exists():
                    for n in range(int((as_today-start).days)+1):
                        date = start + datetime.timedelta(n)
                        if answer.total_score >= 80:
                            Attendance.objects.create(trainees=trainee,
                                                      batches=answer.assessments.batches,
                                                      attendances='present', schedule=date)
                        else:
                            Attendance.objects.create(trainees=trainee,
                                                      batches=answer.assessments.batches,
                                                      attendances='absent', schedule=date)
                    answer.attendance_update = True
                    answer.save()

                elif Attendance.objects.filter(trainees=trainee, batches=answer.assessments.batches).exists():
                    last = max(Attendance.objects.filter(trainees=trainee,
                                                         batches=answer.assessments.batches
                                                         ).values_list("schedule", flat=True))
                    for n in range(int((as_today-last).days)+1):
                        date = last + datetime.timedelta(n)
                        if not Attendance.objects.filter(trainees=trainee,
                                                         batches=answer.assessments.batches,
                                                         attendances='present', schedule=date).exists():
                            if answer.total_score >= 80:
                                Attendance.objects.create(trainees=trainee,
                                                          batches=answer.assessments.batches,
                                                          attendances='present', schedule=date)
                            else:
                                Attendance.objects.create(trainees=trainee,
                                                          batches=answer.assessments.batches,
                                                          attendances='absent', schedule=date)
                    answer.attendance_update = True
                logger.info("attendance was taken")
        logger.error("attendance")
