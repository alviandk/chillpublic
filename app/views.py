from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render_to_response
from django.template import Context, RequestContext
from django.template import Template as template_django
from django.core import serializers
from django.core import urlresolvers
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.contrib import auth
from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode
from django.contrib.auth.decorators import login_required
from django import forms
from django.middleware import csrf
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from accounts.models import *
from captcha.fields import CaptchaField
from api.views import chat_api

import re
import json
import random
import string
import logging


class CaptchaTestForm(forms.Form):
    captcha = CaptchaField()

def get_captcha(request):
    try:
        form = template_django(CaptchaTestForm())
        form = form.render(Context())
    except Exception, err:
        return HttpResponse(err)
    else:
        logging.debug('CAPTCHA content: %s' % form)
    return HttpResponse(form)

def email_to(request, subject, to, msg, fr='ChillPublic <support@chillpublic.com>'):
    try:
        subject = subject
        html_content = msg
        from_email = fr
        to = to
        msg = EmailMessage(subject, html_content, from_email, [to])
        msg.content_subtype = "html"
        msg.send(fail_silently=False)
    except Exception, err:
        logging.exception('\nNotification Mail Failed: Exception: %s\n' % err)
        return False
    else:
        logging.info('\nEmail Status: Success to: %s\n' % to)
    return True

def index(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect('/dashboard')

    plan_list = Plan.objects.all().order_by('order_num')
    return render_to_response('landingpage/index.html', locals(),
                              context_instance=RequestContext(request))


def signup_customer(request):
    def generate_password():
        word = string.digits
        password = ''.join([word[random.randrange(len(word))] for i in range(12)])
        return password

    if request.POST:
        error = []
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email1 = request.POST.get('email1')
        email2 = request.POST.get('email2')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        captcha_check = CaptchaTestForm(request.POST)

        try:
            int(mobile)
        except Exception:
            error.append('mobile')

        if not first_name or not last_name:
            error.append('name')
        if email1 != email2 or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email1):
            error.append('email')
        if password1 != password2 or not password1 or not password2 or not re.match(r'^(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,32}$', password1):
            error.append('password')
        if not captcha_check.is_valid():
            error.append('captcha')

        if error:
            resp = {'status': False, 'msg': error}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            u = User.objects.get(username=email1)
        except Exception:
            try:
                c = Customer.objects.get(mobile_number=mobile)
            except Exception, e:
                u = User.objects.create_user(username=email1, email=email1, password=password1)
                u.is_staff = False
                u.is_superuser = False
                u.is_active = False
                u.first_name = first_name
                u.last_name = last_name
                u.save()

                key = generate_password()
                ca = Customer()
                ca.user = u
                ca.mobile_number = mobile
                ca.email_verification_code = key
                ca.save()
                subject = 'ChillPublic Account Confirmation'
                to = email1
                msg = '''
    <p>Thank you</p>
    <br>
    <p>Please click <a href="http://%s/activate/%s">http://%s/activate/%s</a> to activate your account.</p>

                ''' % (request.META.get('HTTP_HOST'), key, request.META.get('HTTP_HOST'), key)
                email_to(request, subject, to, msg, fr='ChillPublic <support@chillpublic.com>')
            else:
                error.append('exist mobile')
        else:
            error.append('exist email')
        if error:
            resp = {'status': False, 'msg': error}
        else:
            resp = {'status': True, 'msg': error}

        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('landingpage/signup.html', locals(),
                              context_instance=RequestContext(request))

def activation_success(request):
    phone = request.session["phone"]
    return render_to_response('landingpage/activate.html', locals(),
                              context_instance=RequestContext(request))

def registration_success(request):
    return render_to_response('landingpage/registration_success.html', locals(),
                              context_instance=RequestContext(request))


def activate(request, key):
    try:
        ca = Customer.objects.get(email_verification_code=key)
        ca.email_verified = True
        ca.save()
        u = ca.user
        # u.is_active = True
        # u.save()
        request.session['phone'] = ca.mobile_number
        request.session['activation_email'] = u.email
    except Exception:
        try:
            ca = Company.objects.get(email_verification_code=key)
            ca.email_verified = True
            ca.save()
            u = ca.user
            # u.is_active = True
            # u.save()
            request.session['phone'] = ca.phone
            request.session['activation_email'] = u.email
        except Exception:
            return Http404
    return HttpResponseRedirect(reverse('activation_success'))

def pricing(request):
    plan_list = Plan.objects.all().order_by('order_num')
    return render_to_response('landingpage/pricing.html', locals(),
                              context_instance=RequestContext(request))


def signup_company(request):
    def generate_password():
        word = string.digits
        password = ''.join([word[random.randrange(len(word))] for i in range(12)])
        return password

    if request.POST:
        error = []
        company_name = request.POST.get('company_name')
        address = request.POST.get('address')
        category = request.POST.get('category')
        phone = request.POST.get('phone')
        email1 = request.POST.get('email1')
        phone2 = request.POST.get('phone2')
        email2 = request.POST.get('email2')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        captcha_check = CaptchaTestForm(request.POST)

        try:
            int(phone)
        except Exception:
            error.append('phone')

        if not company_name:
            error.append('company_name')
        if not address:
            error.append('address')
        if not category:
            error.append('category')
        if email1 != email2 or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email1):
            error.append('email')
        if password1 != password2 or not password1 or not password2 or not re.match(r'^(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,32}$', password1):
            error.append('password')
        if not captcha_check.is_valid():
            error.append('captcha')
        if error:
            resp = {'status': False, 'msg': error}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            u = User.objects.get(username=email1)
        except Exception:
            try:
                c = Company.objects.get(phone=phone)
            except Exception, e:
                u = User.objects.create_user(username=email1, email=email1, password=password1)
                u.is_staff = False
                u.is_superuser = False
                u.is_active = False
                u.save()

                key = generate_password()
                ca = Company()
                ca.user = u
                ca.company_name = company_name
                ca.phone = phone
                ca.address = address
                ca.email_verification_code = key
                ca.save()
                subject = 'ChillPublic Account Confirmation'
                to = email1
                msg = '''
    <p>Thank you</p>
    <br>
    <p>Please click <a href="http://%s/activate/%s">http://%s/activate/%s</a> to activate your account.</p>

                ''' % (request.META.get('HTTP_HOST'), key, request.META.get('HTTP_HOST'), key)
                email_to(request, subject, to, msg, fr='ChillPublic <support@chillpublic.com>')
            else:
                error.append('exist mobile')
        else:
            error.append('exist email')
        if error:
            resp = {'status': False, 'msg': error}
        else:
            resp = {'status': True, 'msg': error}

        return HttpResponse(json.dumps(resp), content_type='application/json')
    category_list = CategoryCompany.objects.all()
    return render_to_response('landingpage/signup_company.html', locals(),
                              context_instance=RequestContext(request))


@csrf_exempt
def login(request):
    resp = {'status': False, 'msg': 'Bad Request', 'next':request.GET.get('next')}
    if request.POST:
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            cek_auth = auth.authenticate(username=email, password=password)
            auth.login(request, cek_auth)
        except Exception:
            resp = {'status': False, 'msg': 'Account not found.', 'next':request.GET.get('next')}
        else:
            if not request.user.is_active:
                # if request.user.customer:
                try:
                    if request.user.customer.email_verified == False:
                        auth.logout(request)
                        resp = {'status': False, 'msg': 'This account unverified email. Please <a href="/resend-activation-email/">Activate</a> Your Email', 'next':request.GET.get('next')}
                    else:
                        auth.logout(request)
                        resp = {'status': False, 'msg': 'This account unverified mobile phone number. Please <a href="/resend-activation-phone/">Activate</a> Your Mobile Phone Number', 'next':request.GET.get('next')}
                # else:
                except:
                    if request.user.company.email_verified == False:
                        auth.logout(request)
                        resp = {'status': False, 'msg': 'This account unverified email. Please <a href="/resend-activation-email">Activate</a> Your Email', 'next':request.GET.get('next')}
                    else:
                        auth.logout(request)
                        resp = {'status': False, 'msg': 'This account unverified phone number. Please <a href="/resend-activation-phone/">Activate</a> Your Phone Number', 'next':request.GET.get('next')}
                # elif not request.user.is_active:
                # auth.logout(request)
                # resp = {'status': False, 'msg': 'This account unverified. Please <a href="/resend-activation-email">Activate</a> Your Email', 'next':request.GET.get('next')}
            else:
                resp = {'status': True, 'msg': 'Success', 'next':request.GET.get('next')}

    return HttpResponse(json.dumps(resp), content_type='application/json')


def logout(request):
    if request.is_agent:
        z = Agent.objects.get(user = request.user)
        if z.status == '1':
            z.status = ''
        z.is_online = False
        z.active_chat = 0
        z.save()

        # get_ticket = Ticket.objects.filter(assigned__user = request.user, status = '6').update(online = False)
        try:
            get_ticket = Ticket.objects.filter(assigned__user = request.user, status = '6', online = True)
            for list_ticket in get_ticket:
                print(list_ticket.id)
                #send message
                message = '%s leave chat' % request.user
                data = {"user": str(request.user), "message": message, "id": str(list_ticket.id), 'change_status':'True'}
                channnel = "room-" + str(list_ticket.id)
                chat_api(data, channnel)

            
        except Exception,e:
            print(e)
            pass
        update = get_ticket.update(online = False)

    else:
        try:
            # get_ticket = Ticket.objects.filter(author = request.user, status = '6').update(online = False)
            get_ticket = Ticket.objects.filter(author = request.user, status = '6', online = True)
            for list_ticket in get_ticket:
                #send message
                message = '%s leave chat' % request.user
                data = {"user": str(request.user), "message": message, "id": str(list_ticket.id), 'change_status':'True'}
                channnel = "room-" + str(list_ticket.id)
                chat_api(data, channnel)

        except Exception, e:
            print(e)
            pass
        update = get_ticket.update(online = False)

    act = Activity()
    act.user = request.user
    act.text = "last login %s" % request.user.last_login
    act.save()

    auth.logout(request)
    return HttpResponseRedirect('/')


def signup(request):
    return render_to_response('landingpage/signup.html', locals(),
                              context_instance=RequestContext(request))


def resend_activation_email(request):
    def generate_password():
        word = string.digits
        password = ''.join([word[random.randrange(len(word))] for i in range(12)])
        return password


    error = False
    success = False
    msg = ''

    if request.method == 'POST':

        email1 = request.POST.get('email')
        key = generate_password()

        try:
            u = User.objects.get(email=email1)
            if u.customer:
                ca = Customer.objects.get(user = u)
                ca.email_verification_code = key
                ca.save()
                
            else:
                ca = Company.objects.get(user = u)
                ca.email_verification_code = key
                ca.save()


            subject = 'ChillPublic Account Confirmation'
            to = email1
            msg = '''
                <p>Thank you</p>
                <br>
                <p>Please click <a href="http://%s/activate/%s">http://%s/activate/%s</a> to activate your account.</p>

                ''' % (request.META.get('HTTP_HOST'), key, request.META.get('HTTP_HOST'), key)
            email_to(request, subject, to, msg, fr='ChillPublic <support@chillpublic.com>')

            success = True
            msg = 'Please check your email inbox to activate your account.'

        except Exception, e:
            print(e)
            error = True
            msg = 'User Not Found'

    return render_to_response('landingpage/resend-activation.html', locals(), context_instance=RequestContext(request))


def resend_activation_phone(request):

    return render_to_response('landingpage/resend-activation-phone.html', locals(), context_instance=RequestContext(request))
