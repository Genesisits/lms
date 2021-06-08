import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from notifications.models import *
from lms import constants

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'management command for email sending'

    def handle(self, *args, **kwargs):
        mails = EmailNotifications.objects.filter(status=False)
        for mail in mails:
            name = mail.users.first_name + " " + mail.users.last_name
            if mail.required_data != None:
                if mail.template.model == 'USER' and mail.template.purpose == 'created':
                    body = mail.template.body.format(email=mail.required_data['email'],
                                                     password=mail.required_data["password"])
                if mail.template.model == 'BATCH' and mail.template.purpose == 'created':
                    body = mail.template.body.format(batch=mail.required_data['batch'],
                                                     date=mail.required_data['date'],
                                                     bg=mail.required_data['bg'])
                if mail.template.model == 'BATCH' and mail.template.purpose == 'started':
                    body = mail.template.body.format(batch=mail.required_data['batch'],
                                                     bg=mail.required_data['bg'])
                if mail.template.model == 'BATCH' and mail.template.purpose == 'prerequisites':
                    body = mail.template.body.format(batch=mail.required_data['batch'],
                                                     bg=mail.required_data['bg'])
                if mail.template.model == 'BATCH' and mail.template.purpose == 'assessments_list':
                    body = mail.template.body.format(batch=mail.required_data['batch'],
                                                     bg=mail.required_data['bg'])
                if mail.template.model == 'MATERIAL' and mail.template.purpose == 'created':
                    body = mail.template.body.format(batch=mail.required_data['batch'])
                if mail.template.model == 'MATERIAL' and mail.template.purpose == 'approval':
                    body = mail.template.body.format(batch=mail.required_data['batch'],
                                                     status=mail.required_data['status'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'created':
                    body = mail.template.body.format(assessment=mail.required_data['assessment'],
                                                     batch=mail.required_data['batch'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'approval':
                    body = mail.template.body.format(assessment=mail.required_data['assessment'],
                                                     batch=mail.required_data['batch'],
                                                     status=mail.required_data['status'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'activate':
                    if mail.required_data["assessmenttype"] == "objective":
                        asmt_type = "Theortical"
                    elif mail.required_data["assessmenttype"] == "descriptive":
                        asmt_type = "Practical"
                    body = mail.template.body.format(assessmenttype=asmt_type,
                                                     date=mail.required_data['date'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'not_submitted':
                    body = mail.template.body.format(assessment=mail.required_data['assessment'],
                                                     date=mail.required_data['date'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'deadline':
                    body = mail.template.body.format(assessment=mail.required_data['assessment'],
                                                     date=mail.required_data['date'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'required_cutoff':
                    body = mail.template.body.format(user=mail.required_data['user'],
                                                     assessment=mail.required_data['assessment'],
                                                     batch=mail.required_data['batch'])
                if mail.template.model == 'ASSESSMENT' and mail.template.purpose == 'assessment_completed':
                    body = mail.template.body.format(user=mail.required_data['user'],
                                                     assessment=mail.required_data['assessment'],
                                                     batch=mail.required_data['batch'])
            if "password" in body:
                html_content = render_to_string(
                    'register_email.html',
                    {'first_name': name, 'password': 'yes', 'message': body, "value": "."}
                )
            else:
                html_content = render_to_string(
                    'register_email.html',
                    {'first_name': name, 'message': body, "value": "."}
                )
            msg = EmailMultiAlternatives(
                mail.template.subject, constants.EMAIL_MSG, settings.EMAIL_USER, [mail.users.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            mail.status = True
            mail.save()
            logger.info("emails are sent")
        logger.error("emails")
