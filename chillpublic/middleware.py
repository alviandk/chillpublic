# Tokowebku Domain Middleware Handler
#
# Author: Hadi Wijaya (hadi.wijaya@voidsolution.com)

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import Context, Template, RequestContext
from datetime import date, datetime, timedelta
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages

import getpass
import logging
import urllib
import os

from accounts.models import *
from datetime import date, timedelta
from django.middleware import csrf
from django.db import connection
from django.db import transaction

class ChillPublicMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.is_company = False
        request.is_agent = False
        request.is_head = False
        request.is_kyc = False
        try:
            request.notification = Notification.objects.filter(to=request.user, read=False)
        except Exception:
            pass
        try:
            h = HeadCompany.objects.filter(user=request.user)
            if h:
                request.is_head = True
        except Exception:
            pass
        try:
            Company.objects.get(user=request.user)
        except Exception:
            try:
                request.user.agent
            except Exception:
                pass
            else:
                request.is_agent = True

                z = Agent.objects.get(user = request.user)
                z.date_start_leave = None
                z.is_online = True
                z.save()

                request.agent_status = z.status

            try:
                request.name = '%s %s' % (request.user.first_name, request.user.last_name)
            except Exception:
                pass
        else:
            request.is_company = True
            try:
                request.name = request.user.company.company_name
            except Exception:
                pass
        request.settings = settings

        try:
            Customer.objects.get(user=request.user)
        except Exception:
            request.is_customer = False
        else:
            request.is_customer = True

        #kyc user
        try:
            KYCPartner.objects.get(user = request.user)
        except:
            request.is_kyc = False
        else:
            request.is_kyc = True


class SessionIdleTimeout:
    def process_request(self, request):
        if request.user.is_authenticated():
            current_datetime = datetime.now()
            
            if request.session.has_key('last_activity') and (current_datetime - datetime.strptime(request.session['last_activity'], '%Y-%m-%d %H:%M:%S')).seconds > settings.SESSION_IDLE_TIMEOUT:
                logout(request)
            else:
                request.session['last_activity'] = datetime.strftime(current_datetime, '%Y-%m-%d %H:%M:%S')
        return None