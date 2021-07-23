import csv
import logging

from django.core.management.base import BaseCommand

from notifications.models import *

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'create email templates data'

    def add_arguments(self, parser):
        parser.add_argument('path', action='append', type=str)

    def handle(self, *args, **options):
        """ For creating basic email templates """
        # For now data for email templates of csv file is in templates so add path of Lms-User-templates.csv
        with open(options['path'][0]) as f:
            reader = csv.reader(f)
            for row in reader:
                em_templates = EmailTemplates.objects.filter(purpose=row[2], model=row[3])
                if not em_templates:
                    _, created = EmailTemplates.objects.get_or_create(
                        subject=row[0],
                        body=row[1],
                        purpose=row[2],
                        model=row[3],
                    )
                else:
                    em_templates.update(subject=row[0], body=row[1])
                logger.info("templates created")
        logger.error("templates")
