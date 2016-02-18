#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import StringIO
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chillpublic.settings")

from celery import task
from celery.decorators import periodic_task
import json
import getpass
import time

from datetime import datetime, timedelta
from django.template.defaultfilters import slugify
from django.db.models import Count


@task()
def email_to(subject, to, msg, fr='Chillpublic App <support@chillpublic.com>', headers=None):
    from django.core.mail import send_mail, EmailMessage
    try:
        subject = subject
        html_content = msg
        from_email = fr
        to = json.loads(to)
        if headers:
            headers = json.loads(headers)
        else:
            headers = {'Reply-To': 'support@chillpublic.com'}

        msg = EmailMessage(subject, html_content, from_email, to, headers=headers)
        msg.content_subtype = "html"
        msg.send(fail_silently=False)
    except Exception, err:
        logging.exception('\nNotification Mail Failed: Exception: %s\n' % err)
        return False
    else:
        logging.info('\nEmail Status: Success to: %s\n' % to)
    return True


@task()
def mail_notification(subject, to, msg, fr='Chillpublic App <support@chillpublic.com>'):
    from django.core.mail import send_mail, EmailMessage
    try:
        subject = subject
        html_content = msg
        from_email = fr

        msg = EmailMessage(subject, html_content, from_email, to)
        msg.content_subtype = "html"
        msg.send(fail_silently=False)
    except Exception, err:
        logging.exception('\nNotification Mail Failed: Exception: %s\n' % err)
        return False
    else:
        logging.info('\nEmail Status: Success to: %s\n' % to)
    return True
