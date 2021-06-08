import logging
import datetime

from django.core.management.base import BaseCommand

from businessGroup.models import Batch
from businessGroup.views import notify_email

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'activate batch based on batch start_date'

    def handle(self, *args, **kwargs):
        batches = Batch.objects.filter(start_date=datetime.date.today())
        for batch in batches:
            batch.is_active = True
            batch.save()
            if not batch.batch_notification:
                notify_email(module="BATCH", purpose="started", id=batch.id,
                             required_for={"batch": batch.name, "bg": batch.business_group.name})
                batch.batch_notification = True
                batch.save()
                logger.info("batch activated")
        batch = Batch.objects.filter(end_date=datetime.date.today())
        for batches in batch:
            batches.is_active = False
            batches.save()
            logger.info("batch deactivated")
        logger.error("batch activation")
