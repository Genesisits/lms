import logging

from django.core.management.base import BaseCommand

from assessment.models import BatchAssessment


class Command(BaseCommand):
    help = "cta length"

    def handle(self, *args, **options):
        assessments = BatchAssessment.objects.all()
        for assessment in assessments:
            print(assessment.id)
            get_assessment = BatchAssessment.objects.get(id=assessment.id)
            if get_assessment.assessment_data:
                questions = get_assessment.assessment_data
                for question in questions:
                    print(question)
                    if "CTA" in question:
                        if not "answers_length" in question["CTA"]:
                            question["CTA"][0]["answers_length"] = len(question["CTA"][0]["correct_answers"])
                            get_assessment.save()

        return "success"
