from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import Context, RequestContext
from django.template import Template as template_django
from django.template.loader import get_template, render_to_string
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
from django_socketio import broadcast, broadcast_channel, NoSocket
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson
from django.db.models import Avg, Max, Min

from accounts.models import *
from forms import *

from reportlab.pdfgen import canvas
import cStringIO as StringIO
import ho.pisa as pisa
from cgi import escape
from service.tasks import email_to

import os
import re
import json
import random
import string
import urllib2
import logging
from datetime import datetime, timedelta

@login_required
def dashboard(request):
    if request.is_company:
        department_list = request.user.company.departments.all()
        agent_list = request.user.company.agents()
        form_list = request.user.company.forms()
        departement_head_list = request.user.company.heads
        package_list = SiteData.objects.get(company=request.user.company)
        return render_to_response('dashboard/dashboard.html', locals(),
                                  context_instance=RequestContext(request))
    if request.is_agent:
        ticket_list = (Ticket.objects.filter(department__in=[request.user.agent]).select_related('author', 'department', 'comments'))
        subscribe_provider = ServiceProvider.objects.filter(status = 0, product__in=[request.user.agent])
        agent_status = Agent.objects.get(user=request.user).status
        return render_to_response('agent/agent_dashboard.html', locals(),
                                  context_instance=RequestContext(request))

    if request.is_kyc:
        return HttpResponseRedirect('/dashboard/kyc-partner')

    if request.is_head:
        head_company = HeadCompany.objects.get(user=request.user)
        return render_to_response('dashboard/head_dashboard.html', locals(), context_instance=RequestContext(request))

    company_list = Company.objects.filter(user__is_active = True, email_verified = True, phone_verified = True)
    ajax = request.GET.get('ajax')
    if ajax == 'True':

        data    =   render_to_string('dashboard/ajax/customer_dashboard.html', locals(), context_instance=RequestContext(request))
        resp    =   { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')

    else:
        return render_to_response('dashboard/customer_dashboard.html', locals(), context_instance=RequestContext(request))

@login_required
def live_support(request):
    company_list = (Company.objects.select_related('user', 'departments').filter(user__is_active = True, email_verified = True, phone_verified = True))
    ajax = request.GET.get('ajax')

    #ticket type
    ttype = request.GET.get('tlive')

    if ajax == 'True':

        data    = render_to_string('dashboard/ajax/live_support.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')

    else:
        return render_to_response('live_support/live_support.html', locals(), context_instance=RequestContext(request))


@login_required
def live_ticket(request):
    # return HttpResponse(request.user.agent.department)
    # ticket_list = (Ticket.objects.filter(department__in=[request.user.agent.department], status = 1).select_related('author', 'department', 'comments'))
    ticket_list = Ticket.objects.filter(department=request.user.agent.department).exclude(status = '4')
    subscribe_provider = ServiceProvider.objects.filter(status = 1, product__in=[request.user.agent])
    return render_to_response('dashboard/live_ticket.html', locals(), context_instance=RequestContext(request))

@login_required
def agent_service_provider(request):
    # subscribe_provider = ServiceProvider.objects.filter(status = 1, product__in=[request.user.agent])
    subscribe_provider_news = ServiceProvider.objects.filter(status = 0, product__in=[request.user.agent.department])
    subscribe_provider_histories = ServiceProvider.objects.filter(status__in=[1,2], product__in=[request.user.agent.department])
    return render_to_response('dashboard/agent_service_provider.html', locals(), context_instance=RequestContext(request))

@login_required
def agent_change_status(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        status = request.POST.get('status')
        day_on_leave = request.POST.get('day_on_leave')
        agent_id = request.POST.get('agent')

        try:
            agent = Agent.objects.get(user=agent_id)

            agent.status = status

            if status:
                agent.is_online = True

            agent.day_on_leave = day_on_leave
            agent.save()
        except Exception, e:
            resp = { 'status': False, 'msg': unicode(e) }
        else:
            if status == "1":
                act = Activity()
                act.user = request.user
                act.text = "updated status to away"
                act.save()
            elif status == "2":
                act = Activity()
                act.user = request.user
                act.text = "updated status to on leave"
                act.save()
            else:
                act = Activity()
                act.user = request.user
                act.text = "updated status to online"
                act.save()
            
            resp = { 'status': True, 'msg': 'Success' }

        return HttpResponse(json.dumps(resp), content_type='application/json')

def render_to_pdf(template_src, context_dict, request):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()

    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result, link_callback=fetch_resources, encoding="utf-8")
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def fetch_resources(uri, rel):
    path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    return path


@login_required
def create_pdf(request):
    if request.is_agent:
        obj                         = KYCInformation.objects.get(user__username = request.GET.get('username'))
    else:
        obj                         = KYCInformation.objects.get(user__username = request.user.username)
    get_contact_detail          = obj.contact_details
    split_get_contact_detail    = get_contact_detail.split(",")
    telp                        = split_get_contact_detail[0]
    mobile                      = split_get_contact_detail[1]
    email                       = split_get_contact_detail[2]
    get_permanent_address       = obj.permanent_address
    split_permanent_address     = get_permanent_address.split("||")
    address                     = split_permanent_address[0]
    city                        = split_permanent_address[1]
    pin_code                    = split_permanent_address[2]
    state                       = split_permanent_address[3]
    country                     = split_permanent_address[4]
    image                       = obj.photograph

    if request.is_agent:
        get_department              = Department.objects.get(name = request.user.agent.department)
        company                     = Company.objects.get(departments = get_department)
    else:
        company = ''

    # return HttpResponse(company)
    return render_to_pdf(
            'pdfgen.html',
            {
                'pagesize':'A4',
                'obj': obj,
                'telp':telp,
                'mobile':mobile,
                'email':email,
                'address': address,
                'city': city,
                'pin_code': pin_code,
                'state': state,
                'country': country,
                'user': request.user,
                'company': company,
            },
            request
        )

@login_required
def kyc_verification(request):

    ajax = request.GET.get('ajax')
    service_providers= ServiceProvider.objects.filter(user = request.user)

    try:
        get_kyc_instruction = KYCInstruction.objects.latest('id')
    except Exception, e:
        pass

    success = False
    show_form = False
    
    try:
        cek_kyc = KYCInformation.objects.get(user = request.user)

        if request.method == 'POST':
            form = KYCForm(request.POST, request.FILES, user=request.user, instance = cek_kyc)
            if form.is_valid():
                obj = form.save()
                success = True
                if request.is_ajax():
                    return HttpResponse('success')
                else:
                    return HttpResponseRedirect('/dashboard/kyc/')
            else:
                if request.is_ajax():
                    errors = form.errors
                    return HttpResponse(simplejson.dumps(errors))
                else:
                    show_form = True
        else:
            get_contact_detail          = cek_kyc.contact_details
            split_get_contact_detail    = get_contact_detail.split(",")
            get_permanent_address       = cek_kyc.permanent_address
            split_permanent_address     = get_permanent_address.split("||")
            form = KYCForm(instance = cek_kyc, initial={'residence_address': cek_kyc.residence_address, 
                'contact_details_tel': split_get_contact_detail[0],
                'contact_details_mobile': split_get_contact_detail[1],
                'contact_details_email': split_get_contact_detail[2],
                'permanent_address': split_permanent_address[0],
                'city1': split_permanent_address[1],
                'pin_code1': split_permanent_address[2],
                'state1': split_permanent_address[3],
                'country1': split_permanent_address[4]})
    
    except:
        if request.method == 'POST':
            form = KYCForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                obj = form.save()
                success = True
                if request.is_ajax():
                    return HttpResponse('success')
                    # return HttpResponseRedirect('/dashboard/kyc/')
                else:
                    return HttpResponseRedirect('/dashboard/kyc/')

            else:
                if request.is_ajax():
                    errors = form.errors
                    return HttpResponse(simplejson.dumps(errors))
                else:
                    show_form = True
        else:
            form = KYCForm()

    try:
        kyc_instruction = KYCInstruction.objects.get(id = 1)
    except:
        pass
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        # return render_to_response('dashboard/ajax/kyc.html', locals(), context_instance=RequestContext(request))
        data    = render_to_string('dashboard/ajax/kyc.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/kyc_verification.html', locals(), context_instance=RequestContext(request))



@login_required
def get_department_ajax(request):
    company_key = request.GET.get('key')
    try:
        # department_list = Company.objects.get(id=company_key).departments.all()
        department_list = (Company.objects.select_related('user', 'departments').get(id = company_key).departments.all())
    except Exception:
        department_list = []
    return render_to_response('dashboard/ajax/department_list.html', locals(),
                          context_instance=RequestContext(request))

@login_required
def profile(request):
    time_now = datetime.now()
    less = time_now - timedelta(days=7)
    activities = Activity.objects.filter(user=request.user, created_at__gte=less, created_at__lte=time_now).order_by('-created_at')[:10]
    ajax = request.GET.get('ajax')
    icon_btn = request.GET.get('icon_btn')
    if ajax == 'True':
        # return render_to_response('dashboard/profile_customer.html', locals(), context_instance=RequestContext(request))
        data    = render_to_string('dashboard/profile_customer.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/profile.html', locals(), context_instance=RequestContext(request))

@login_required
def tickets(request):
    if request.is_agent:
        ticket_list = Ticket.objects.filter(department=request.user.agent.department).exclude(status = '4').order_by('-id')
    else:
        ticket_list = Ticket.objects.filter(author=request.user).exclude(status = '4').order_by('-id')
    # return render_to_response('dashboard/tickets.html', locals(), context_instance=RequestContext(request))
    ticket_type = Ticket().STATUS_CHOICE
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        # return render_to_response('ticket/tickets_customer.html', locals(), context_instance=RequestContext(request))
        data    = render_to_string('ticket/tickets_customer.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('ticket/tickets.html', locals(), context_instance=RequestContext(request))

@login_required
def escalated_tickets(request):
    if request.is_head:
        ticket_list = Ticket.objects.filter(status='2', department__in=[i.id for i in request.user.head_company.departments.all()])
    else:
        return HttpResponseRedirect('/')
    return render_to_response('ticket/escalated_ticket.html', locals(), context_instance=RequestContext(request))

@login_required
def resolved(request):
    resolved_list = Ticket.objects.filter(author=request.user, status="3")
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        # return render_to_response('dashboard/ajax/resolved.html', locals(),context_instance=RequestContext(request))
        data    = render_to_string('dashboard/ajax/resolved.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/resolved.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def forms_customer(request):
    company_list = Company.objects.all()
    ajax = request.GET.get('ajax')
    company_id = request.GET.get('company')
    department_id = request.GET.get('department')
    value_select_form = request.GET.get('value_select_form')
    if ajax == 'True':
        # return render_to_response('dashboard/ajax/form_customer.html', locals(),context_instance=RequestContext(request))
        data    = render_to_string('dashboard/ajax/form_customer.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/forms_customer.html', locals(),context_instance=RequestContext(request))

@login_required
def customer_ticket_create(request):
    if request.POST:
        form = request.POST.get('form_id')
        form_value = request.POST.get('form_value')
        department = request.POST.get('department')

        try:
            ticket_id = len(Ticket.objects.all()) + 1
            d = Department.objects.get(id=department)
            form = Forms.objects.get(id=form)
            form_customer = FormCustomer()
            form_customer.user = request.user
            form_customer.form_value = form_value
            form_customer.save()
            form.form_customers.add(form_customer)

            agents = Agent.objects.filter(department=d).exclude(status='2')

            data_dict = dict()

            for i in agents:
                data_dict[i.user] = i.total_assigned
                
            data_lowest = sorted(data_dict)[0]
            agent_user = data_lowest

            assigned = AssignedUser.objects.create(user = agent_user, timestamp = datetime.now())
            text_comment = '%s %s change status to Assigned' % (agent_user.first_name, agent_user.last_name)
            try:
                c = Comment()
                c.user = agent_user
                c.text = text_comment
                c.timestamp = datetime.now()
                c.save()

                t = Ticket()
                t.author = request.user
                t.department = d
                t.title = "%s %s %s" % (form.name, d.name, ticket_id)
                t.timestamp = datetime.now()
                t.assigned = assigned
                t.status = '6'
                t.save()
                t.comments.add(c)

                r = TimetoResolve()
                r.ticket = t
                r.time = 96
                r.due = datetime.now()
                r.save()

                act = Activity()
                act.user = request.user
                act.text = "submit new service/application forms"
                act.save()

                resp = {'status': True, 'msg': 'success', 'form_customer_id': form_customer.id }
            except Exception, e:
                resp = {'status': False, 'msg': unicode(e)}
                
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            resp = {'status': True, 'msg': 'success', 'form_customer_id': form_customer.id }
        return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def form_customer_edit(request):
    if request.POST:
        form_customer_id = request.POST.get('form_customer_id')
        file_form = request.FILES.get('file')
        label = request.POST.get('label')

        try:
            form_customer = FormCustomer.objects.get(id=form_customer_id)
            file_form_customer = FileFormCustomer()
            file_form_customer.label_file = label
            file_form_customer.file_name = file_form
            file_form_customer.save()
            form_customer.file_form_customers.add(file_form_customer)
            # form_customer.save()
                
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def forms_company(request):
    form_list = Forms.objects.filter(company=Company.objects.get(user=request.user))
    return render_to_response('dashboard/forms_company.html', locals(),
                              context_instance=RequestContext(request))


@login_required
def agents(request):
    department_id = request.GET.get('department')
    from_url = request.GET.get('from')
    if department_id:
        department = Department.objects.get(id=department_id)
        existing_agent_list = department.get_agents()
        # if request.is_company:
        #     agent_list = request.user.company.agents_request()
        #     existing_agent_list = request.user.company.agents()
        # if request.is_head:
        #     department_list = request.user.head_company.departments.all()
        #     agent_list = request.user.head_company.agents_request()
        #     existing_agent_list = request.user.head_company.agents()
    else:
        if request.is_company:
            department_list = request.user.company.departments.all()
            agent_list = request.user.company.agents_request()
            existing_agent_list = request.user.company.agents()
        if request.is_head:
            department_list = request.user.head_company.departments.all()
            agent_list = request.user.head_company.agents_request()
            existing_agent_list = request.user.head_company.agents()

    return render_to_response('dashboard/agents.html', locals(), context_instance=RequestContext(request))


@login_required
def departments(request):
    department_id = request.GET.get('department')
    department_perform_id = request.GET.get('department_perform')
    if department_id or department_perform_id:

        department = department_id or department_perform_id

        department_list = Department.objects.filter(id=department)
    else:
        if request.is_company:
            department_list = request.user.company.departments.all()
        if request.is_head:
            department_list = request.user.head_company.departments.all()

    return render_to_response('dashboard/departments.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def company_heads(request):
    head_list = request.user.company.heads.all()
    return render_to_response('dashboard/company_heads.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def company_heads_create(request):
    department_list = request.user.company.departments.all()
    if request.POST:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        email = request.POST.get('email')
        repassword = request.POST.get('repassword')
        department = json.loads(request.POST.get('department'))

        if not first_name or not last_name:
            resp = {'status': False, 'msg': 'Please check again your name'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not email or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email):
            resp = {'status': False, 'msg': 'Please check again your email'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if password != repassword:
            resp = {'status': False, 'msg': 'Please check password'}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            u = User.objects.create_user(username=email, email=email, password=password)
            u.is_staff = False
            u.is_superuser = False
            u.is_active = True
            u.first_name = first_name
            u.last_name = last_name
            u.save()
            h = HeadCompany()
            h.user = u
            h.save()
            for i in department:
                d = Department.objects.get(id=i)
                h.departments.add(d)
            h.save()
            c = request.user.company
            c.heads.add(h)
            c.save()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "created department heads"
            act.save()

            resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/company_heads_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def company_heads_edit(request, key):
    lookup = HeadCompany.objects.get(id=key)
    department_list = request.user.company.departments.all()
    if request.POST:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        email = request.POST.get('email')
        repassword = request.POST.get('repassword')
        department = json.loads(request.POST.get('department'))
        if not first_name or not last_name:
            resp = {'status': False, 'msg': 'Please check again your name'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not email or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email):
            resp = {'status': False, 'msg': 'Please check again your email'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if password != repassword and password and repassword:
            resp = {'status': False, 'msg': 'Please check password'}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            h = lookup
            u = h.user
            u.is_staff = False
            u.is_superuser = False
            u.is_active = True
            u.email = email
            u.username = email
            u.first_name = first_name
            u.last_name = last_name
            u.save()
            if password:
                u.set_password(password)
                u.save()
            h.save()
            h.departments.clear()
            for i in department:
                d = Department.objects.get(id=i)
                h.departments.add(d)
            h.save()
        except Exception, err:
            logging.exception('\n\n\n %s \n\n\n' % err)
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "updated department heads"
            act.save()

            resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/company_heads_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def company_heads_delete(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            Agent.objects.get(id=key).delete()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            act = Activity()
            act.user = request.user
            act.text = "deleted department heads"
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def agent_create(request):
    if request.is_company:
        department_list = request.user.company.departments.all()
    if request.is_head:
        department_list = request.user.head_company.departments.all()
        
    if request.POST:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        email = request.POST.get('email')
        repassword = request.POST.get('repassword')
        department = request.POST.get('department')
        mobile = request.POST.get('mobile')
        if not first_name or not last_name:
            resp = {'status': False, 'msg': 'Please check again your name'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not email or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email):
            resp = {'status': False, 'msg': 'Please check again your email'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if password != repassword:
            resp = {'status': False, 'msg': 'Please check password'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not mobile:
            resp = {'status': False, 'msg': 'Please check mobile phone number'}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            d = Department.objects.get(id=department)

            ar = AgentRequest()
            ar.department = d
            ar.email = email
            ar.phone = mobile
            ar.first_name = first_name
            ar.last_name = last_name
            ar.password = password
            ar.save()

            notif = Notification.objects.create(timestamp = datetime.now(), notif_type = 3, to = request.user.head_company.heads_company.all()[0].user, ref_id = ar.id)

        except Exception, err:
            AgentRequest.objects.get(id=ar.id).delete()

            Notification.objects.get(id=notif.id).delete()

            resp = {'status': False, 'msg': unicode(err)}
        else:
            act = Activity()
            act.user = request.user
            act.text = "created new request agents %s %s" % (first_name, last_name)
            act.save()

            company_mail = [ar.get_mail_company()]
            company_mail = ['hadi@tokowebku.com']
            # company_mail = ['m.hidayatulloh1@gmail.com']
            subject = 'Agent Request Approval'
            msg = '''
<p>You have notify for agent create request:</p>
<p>EMAIL: %s</p>
<p>FIRST NAME: %s</p>
<p>LAST NAME: %s</p>
<p>DEPARTMENT: %s</p>
''' % (email, first_name, last_name, d.name)
            email_to.delay(subject, json.dumps(company_mail), msg, fr='ChillPublic <support@chillpublic.com>')

            resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/agent_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def agent_edit(request, key):
    lookup = Agent.objects.get(id=key)
    if request.is_company:
        department_list = request.user.company.departments.all()
    if request.is_head:
        department_list = request.user.head_company.departments.all()
        
    if request.POST:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        email = request.POST.get('email')
        repassword = request.POST.get('repassword')
        department = request.POST.get('department')
        mobile = request.POST.get('mobile')
        if not first_name or not last_name:
            resp = {'status': False, 'msg': 'Please check again your name'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not email or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email):
            resp = {'status': False, 'msg': 'Please check again your email'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if password != repassword and password and repassword:
            resp = {'status': False, 'msg': 'Please check password'}
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not mobile:
            resp = {'status': False, 'msg': 'Please check mobile phone number'}
            return HttpResponse(json.dumps(resp), content_type='application/json')

        try:
            d = Department.objects.get(id=department)
            a = lookup
            u = a.user
            u.first_name = first_name
            u.last_name = last_name
            u.email = email
            u.username = email
            a.department = d
            a.phone = mobile
            if password:
                u.set_password(password)
            u.save()
            a.save()
        except Exception, err:
            logging.exception('\n\n\n %s \n\n\n' % err)
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "updated agents %s %s" % (first_name, last_name)
            act.save()

            resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/agent_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def agent_delete(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            agent = Agent.objects.get(id=key)

            ar = agent.agentrequest_set.all()[0]
            ar.delete()

            agent.delete()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "deleted agents %s %s" % (agent.user.first_name, agent.user.last_name)
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def agent_perform(request, key):

    try:
        agent = Agent.objects.get(id=key)
    except Exception, e:
        return HttpResponseRedirect(reverse('agents'))

    return render_to_response('agent/agent_performance.html', locals(), context_instance=RequestContext(request))
    # lookup = Agent.objects.get(id=key)

@login_required
def request_agent_delete(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            agent = AgentRequest.objects.get(id=key)
            # agent.user.delete()
            agent.delete()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "deleted request agents"
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def request_agent_approve(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            agent = AgentRequest.objects.get(id=key)

            user = User.objects.create_user(username=agent.email, email=agent.email, password=agent.password)
            user.first_name = agent.first_name
            user.last_name = agent.last_name
            user.save()

            a = Agent()
            a.user = user
            a.department = agent.department
            a.save()

            agent.agent = a
            agent.status = 1
            agent.save()

            company_mail = [agent.get_mail_head()]
            company_mail = ['hadi@tokowebku.com']
            subject = 'The agent request already approved'
            msg = '''
<p>You have notify for agent approved request:</p>
<p>EMAIL: %s</p>
<p>FIRST NAME: %s</p>
<p>LAST NAME: %s</p>
<p>DEPARTMENT: %s</p>
''' % (agent.email, agent.first_name, agent.last_name, agent.department.name)
            email_to.delay(subject, json.dumps(company_mail), msg, fr='ChillPublic <support@chillpublic.com>')
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "approved request agents"
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def request_agent_remove(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            agent = Agent.objects.get(id=key)
            agent.request_remove = True
            agent.save()

            ar = agent.agentrequest_set.all()[0]

            # company_mail = [ar.get_mail_company()]
            # company_mail = ['hadi@tokowebku.com']
            company_mail = ['m.hidayatulloh1@gmail.com']
            subject = 'Agent Request Remove'
            msg = '''
<p>You have notify for agent remove request:</p>
<p>EMAIL: %s</p>
<p>FIRST NAME: %s</p>
<p>LAST NAME: %s</p>
<p>DEPARTMENT: %s</p>
''' % (ar.email, ar.first_name, ar.last_name, ar.department.name)
            email_to.delay(subject, json.dumps(company_mail), msg, fr='ChillPublic <support@chillpublic.com>')
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:

            act = Activity()
            act.user = request.user
            act.text = "deleted request agents"
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def department_create(request):
    if request.POST:
        name = request.POST.get('name')
        description = request.POST.get('description')
        try:
            d = request.user.company.departments.get(name=name)
        except Exception:
            d = Department()
            d.name = name
            d.description = description
            d.save()

            if request.is_company:
                c = request.user.company
            if request.is_head:
                c = request.user.head_company
            c.departments.add(d)
            c.save()

            act = Activity()
            act.user = request.user
            act.text = "created new departments %s" % name
            act.save()

            resp = {'status': True, 'msg': 'success'}
        else:
            resp = {'status': False, 'msg': 'exist'}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/department_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def department_edit(request, key):
    lookup = Department.objects.get(id=key)
    if request.POST:
        name = request.POST.get('name')
        description = request.POST.get('description')
        try:
            d = lookup
        except Exception:
            resp = {'status': False, 'msg': 'Not Found'}
        else:
            d.name = name
            d.description = description
            d.save()
            resp = {'status': True, 'msg': 'success'}

            act = Activity()
            act.user = request.user
            act.text = "updated departments %s" % name
            act.save()

        return HttpResponse(json.dumps(resp), content_type='application/json')

    return render_to_response('dashboard/department_form.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def department_delete(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            Department.objects.get(id=key).delete()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            act = Activity()
            act.user = request.user
            act.text = "deleted departments"
            act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def department_perform(request, key):

    try:
        department = Department.objects.get(id=key)
    except Exception, e:
        return HttpResponseRedirect(reverse('departments'))

    return render_to_response('dashboard/department_performance.html', locals(), context_instance=RequestContext(request))

def form_parser(data):
    from pyquery import PyQuery as pq
    d = pq(data)
    result = []
    for i in d('.component'):
        c = pq(i.attrib['data-content'])
        for item in c('.field').items():
            pq(item)
        json_data = {
            'title': i.attrib['data-title'],
            'fields': {
                'id':'x'
            }
        }
        result.append(json_data)
    return result


@login_required
def form_create(request):
    if request.POST:
        form_title = request.POST.get('form_title')
        form_content = request.POST.get('form_content')
        type_form = request.POST.get('type_form')
        form_department = request.POST.get('form_department')

        # json_data = form_parser(form_content)
        # resp = {'status': False, 'msg': json_data}
        #return HttpResponse(json.dumps(resp), content_type='application/json')

        f = Forms()
        f.name = form_title
        f.company = Company.objects.get(user=request.user)
        f.form_content = form_content
        f.type_form = type_form
        f.department_id = form_department
        f.save()
        resp = {'status': True, 'msg': 'success'}

        act = Activity()
        act.user = request.user
        act.text = "created forms"
        act.save()

        return HttpResponse(json.dumps(resp), content_type='application/json')

    # return render_to_response('dashboard/forms_form.html', locals(),
    #                           context_instance=RequestContext(request))
    department_list = request.user.company.departments.all()
    type_form_choices = Forms.TYPE_FORM_CHOICE
    return render_to_response('form_builder/index.html', locals(), context_instance=RequestContext(request))

@login_required
def form_edit(request, key):
    if request.POST:
        form_title = request.POST.get('form_title')
        form_content = request.POST.get('form_content')
        type_form = request.POST.get('type_form')
        form_department = request.POST.get('form_department')

        form = Forms.objects.get(id=key)
        form.name = form_title
        form.form_content = form_content
        form.type_form = type_form
        form.department_id = form_department
        form.save()

        act = Activity()
        act.user = request.user
        act.text = "updated forms"
        act.save()

        resp = {'status': True, 'msg': 'success'}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    lookup = Forms.objects.get(id=key)
    department_list = request.user.company.departments.all()

    type_form_choices = Forms.TYPE_FORM_CHOICE

    return render_to_response('form_builder/index.html', locals(), context_instance=RequestContext(request))

@login_required
def form_delete(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST:
        key = request.POST.get('key')
        try:
            Forms.objects.get(id=key).delete()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            act = Activity()
            act.user = request.user
            act.text = "deleted forms"
            act.save()
            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def get_form_json(request):
    json_data_input = open('media/js/form_builder/data/input.json')
    json_data_select = open('media/js/form_builder/data/select.json')
    json_data_radio = open('media/js/form_builder/data/radio.json')
    json_data_button = open('media/js/form_builder/data/buttons.json')
    data_input = json.load(json_data_input)
    data_select = json.load(json_data_select)
    data_radio = json.load(json_data_radio)
    data_button = json.load(json_data_button)

    resp = { 'input': data_input, 'select': data_select, 'radio': data_radio, 'button': data_button }
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def get_form_ajax(request):
    department_key = request.GET.get('department')
    company_key = request.GET.get('company')
    form_type = request.GET.get('form_type')
    try:
        form_list = Forms.objects.filter(company_id=company_key, department_id=department_key, type_form=form_type)
    except Exception:
        form_list = []
    return render_to_response('dashboard/ajax/form_list.html', locals(),
                          context_instance=RequestContext(request))

@login_required
def get_form_save(request):
    resp = { 'status': False, 'msg': "Bad Request" }
    if request.POST:
        form_id = request.POST.get('form_id')
        form = Forms.objects.get(id=form_id)
        resp = { 'status': True, 'form_field': form.form_content }
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def packages(request):
    if request.is_company:
        company_plan = SiteData.objects.get(company=request.user.company)
    package_list = Plan.objects.all().order_by('order_num')
    return render_to_response('dashboard/packages.html', locals(),
                              context_instance=RequestContext(request))

@login_required
def change_packages(request):
    resp = { 'status': False }
    if request.POST:
        plan_id = request.POST.get('plan_id')
        company = request.POST.get('company')
        plan_month = request.POST.get('plan_month')
        status = "Change"
        plan_package = Plan.objects.get(id=plan_id)
        site_data = SiteData.objects.get(company=company)
        site_data.status = status
        site_data.request_plan = plan_package.name
        site_data.subscribe_plan = plan_month
        site_data.save()

        resp = { 'status': True }
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def profile_save(request):
    if request.POST:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name')
        address = request.POST.get('address')
        company_logo = request.FILES.get('company_logo')
        photo = request.FILES.get('photo')
        try:
            if request.is_customer or request.is_agent or request.is_head:
                u = request.user
                u.first_name = first_name
                u.last_name = last_name
                u.email = email
                u.username = email
                if password:
                    u.set_password(password)
                u.save()
                if request.is_head:
                    h = HeadCompany.objects.get(user=request.user)
                    h.address = address
                    if photo:
                        h.photo = photo
                    h.save()
                if request.is_agent:
                    a = Agent.objects.get(user=request.user)
                    a.address = address
                    if photo:
                        a.photo = photo
                    a.save()
                if request.is_customer:
                    c = Customer.objects.get(user=request.user)
                    c.address = address
                    if photo:
                        c.photo = photo
                    c.save()

                if password and photo:
                    act = Activity()
                    act.user = request.user
                    act.text = "updated photo and changed password"
                    act.save()
                else:
                    if password:
                        act = Activity()
                        act.user = request.user
                        act.text = "changed password"
                        act.save()
                    elif photo:
                        act = Activity()
                        act.user = request.user
                        act.text = "updated photo"
                        act.save()
                    else:
                        act = Activity()
                        act.user = request.user
                        act.text = "updated profile"
                        act.save()

            else:
                u = request.user
                u.email = email
                u.username = email
                if password:
                    u.set_password(password)
                u.save()
                if request.is_company:
                    c = Company.objects.get(user=request.user)
                    c.company_name = company_name
                    c.address = address
                    if company_logo:
                        c.logo = company_logo
                    c.save()

                if password and company_logo:
                    act = Activity()
                    act.user = request.user
                    act.text = "updated company logo and changed password"
                    act.save()
                else:
                    if password:
                        act = Activity()
                        act.user = request.user
                        act.text = "changed password"
                        act.save()
                    elif company_logo:
                        act = Activity()
                        act.user = request.user
                        act.text = "updated company logo"
                        act.save()
                    else:
                        act = Activity()
                        act.user = request.user
                        act.text = "updated profile"
                        act.save()

        except Exception, err:
            error = unicode(err)
            return render_to_response('dashboard/profile.html', locals(), context_instance=RequestContext(request))
    if request.is_ajax():
        return HttpResponse('ok')
    else:
        return HttpResponseRedirect(reverse('profile'))



@login_required
def ticket_create(request):

    company_list = Company.objects.filter(user__is_active = True, email_verified = True, phone_verified = True)

    if request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        company = request.POST.get('company')
        department = request.POST.get('department')
        ticket_type = request.POST.get('live')

        #Multiple Live Chat Request from Customer to Same Company Same Department shouldn't be allowed
        check_department = Ticket.objects.filter(department__id = department, online = True)
        if len(check_department) > 0 and ticket_type == '1':
            check_department = Ticket.objects.get(department__id = department, online = True)
            resp = {'status': False, 'msg': 'Forbidden', 'code':'403'}
        else:

            try:
                d = Department.objects.get(id=department)
                t = Ticket()
                t.author = request.user
                t.department = d
                t.title = title
                t.description = description
                t.timestamp = datetime.now()

                if ticket_type == '1':
                    t.live = True
                else:
                    t.live = False


                message_info = ''
                code = ''
                #check agent handle ticket
                if ticket_type == '1':

                    #check customer active live chat
                    if 'chat_id' not in request.session or not request.session['chat_id'] or len(request.session['chat_id']) <= 2:

                        #check how many customer ticket is live with same department
                        customer_check = Ticket.objects.filter(author = request.user, department = d, online = True)
                        if len(customer_check) <= 3:

                            q = Agent.objects.filter(department = d, is_online = True).values('user').annotate(Min('active_chat'))

                            if len(q) > 0:
                                if min(q)['active_chat__min'] < 3:
                                    get_user_id = min(q)['user']
                                    get_user = User.objects.get(id = get_user_id)
                                    t.assigned = AssignedUser.objects.create(user = get_user)
                                    t.status = '6'

                                    #update agent active chat
                                    agent_chat = Agent.objects.get(user = get_user)
                                    agent_chat.active_chat = agent_chat.active_chat + 1
                                    agent_chat.save()

                                    #set active online chat
                                    t.online = True
                                else:
                                    code = 'busy'
                                    message_info = "All Agents are Busy, Waiting for 120 Seconds....Or Offline Ticket"
                            else:
                                pass
                        else:
                            message_info = "You can't create live ticket with same department in same time"
                    else:
                        message_info = 'Max 3 active chat in same time, your ticket will be offline ticket'

                else:
                    list_agent = []
                    q = Agent.objects.filter(department = d, is_online = True)
                    for data in q:
                        list_agent.append(data.user)


                    #check number agent online
                    try:
                        if len(q) > 0:

                            #check assigned ticket
                            list_agent_assigned = []
                            q1 = Ticket.objects.filter(department = d)
                            for data in q1:
                                try:
                                    list_agent_assigned.append(data.assigned.user)
                                except:
                                    pass


                            if len(list_agent) != len(set(list_agent_assigned)):
                                for data in list_agent:
                                    if data not in list_agent_assigned:
                                        get_user = User.objects.get(username = data)
                                t.assigned = AssignedUser.objects.create(user = get_user)
                                t.status = '6'
                                # broadcast_channel('new', channel="room-3")
                                
                            else:
                                stats = dict((i,list_agent_assigned.count(i)) for i in list_agent_assigned if list_agent_assigned.count(i) < 3 and i in list_agent)
                                if len(stats) > 0:
                                    data = min(stats.iterkeys(), key=lambda k: stats[k])
                                    get_user = User.objects.get(username = data)
                                    t.assigned = AssignedUser.objects.create(user = get_user)
                                    t.status = '6'
                                    # broadcast_channel('new', channel="room-3")
                                else:
                                    pass

                        else:
                            pass
                    except Exception, e:
                        print(e)

                new_ticket = t.save()

                #set default time for assigned ticket state
                if t.status == '6':
                    print(request.POST.get('company'))
                    try:
                        company_setting_time = CompanySettings.objects.get(company__id = request.POST.get('company'))
                        TimetoResolve.objects.create(ticket = t, time = company_setting_time.time_to_resolve)
                    except Exception, e:
                        print(e)


                if t.online == True:
                    try:
                        data = {"agent": str(t.assigned.user), "id": t.id}
                        broadcast_channel(data, channel="channel-"+str(t.assigned.user.id))
                        # print(str(t.assigned.user.id))
                    except:
                        pass
                
            except Exception, err:
                resp = {'status': False, 'msg': unicode(err), 'key':''}
            else:
                if len(Agent.objects.filter(department = d, is_online = True)) > 0:
                    if code == 'busy':
                        resp = {'status': True, 'msg': 'success', 'key':t.id, 'is_online': t.online, 'code':code}
                    else:
                        resp = {'status': True, 'msg': 'success', 'key':t.id, 'message_info': message_info, 'is_online': t.online, }
                else:
                    t.live = False
                    t.save()
                    message_info = 'All Agents are Offline - Creating <a href="/dashboard/tickets/view1/?id='+str(t.id)+'">Offline Ticket</a>'
                    resp = {'status': True, 'msg': 'success', 'key':t.id, 'message_info': message_info, 'is_online': t.online}
            # return HttpResponseRedirect(reverse('tickets'))

        act = Activity()
        act.user = request.user
        if ticket_type == '1':
            act.text = "create live support"
        else:
            act.text = "create offline ticket"
        act.save()

        return HttpResponse(json.dumps(resp), content_type='application/json')

    # return render_to_response('dashboard/department_form.html', locals(), context_instance=RequestContext(request))
    return render_to_response('ticket/ticket_create.html', locals(), context_instance=RequestContext(request))


from api.views import chat_api
@login_required
def comment_create(request):
    if len(str(request.user.get_full_name())) > 0:
        user = str(request.user.get_full_name())
    else:
        user = str(request.user.username)
    if request.POST:
        ticket_id = request.POST.get('id')
        text = request.POST.get('text')

        try:
            data = {"user": user, "message": text, "id": ticket_id}
            channnel = "room-" + ticket_id
            chat_api(data, channnel)
        except Exception, e:
            print(e)

        try:
            t = Ticket.objects.get(id=ticket_id)
            c = Comment()
            c.user = request.user
            c.text = text
            c.timestamp = datetime.now()
            c.save()
            t.comments.add(c)
            t.save()
            i = c

            act = Activity()
            act.user = request.user
            act.text = "create new comment"
            act.save()
        except:
            pass
    return HttpResponse(channnel)


@login_required
def remove_session(request):
    try:
        key = request.GET.get('id')
        if request.is_agent:
            save_list = request.session['chat_id']
            save_list.remove(key)
            request.session['chat_id'] = save_list
            t = Agent.objects.get(user = request.user)
            t.active_chat = t.active_chat - 1
            t.save()
        else:
            del request.session['chat_id']

        #set false online ticket
        ticket = Ticket.objects.get(id = key)
        ticket.online = False
        ticket.save()

        #send message
        # if request.is_agent:
        #     message = '%s leave chat' % request.user
        # else:
        #     message = '%s leave chat' % request.user
        if len(str(request.user.get_full_name())) > 0:
            get_user = str(request.user.get_full_name())
        else:
            get_user = str(request.user.username)
        message = '%s leave chat' % get_user
        data = {"user": str(request.user), "message": message, "id": key, 'change_status':'True'}
        channnel = "room-" + key
        chat_api(data, channnel)

        return HttpResponse('remove_session')
    except Exception, e:
        return HttpResponse('error')

@login_required
def notification(request):
    read_notification = Notification.objects.filter(to=request.user, read=True).order_by('-id')
    unread_notification = Notification.objects.filter(to=request.user, read=False).order_by('-id')
    return render_to_response('dashboard/notification.html', locals(),context_instance=RequestContext(request))

@login_required
def ticket_view(request):
    key = request.GET.get('id')
    try:
        # lookup            = (Ticket.objects.select_related('author').get(id = key))
        lookup            = (Ticket.objects.select_related('author').get(id = key, online = True))
        if lookup.status != '4':
            # if request.is_agent:
            if 'chat_id' not in request.session or not request.session['chat_id']:
                request.session['chat_id'] = [key]
            else:
                save_list = request.session['chat_id']
                if key not in save_list:
                    save_list.append(key)
                else:
                    pass
                request.session['chat_id'] = save_list
        else:
            del request.session['chat_id']
    except Exception, err:
        return HttpResponseRedirect(reverse('tickets'))
    return render_to_response('ticket/ticket_detail.html', locals(),context_instance=RequestContext(request))


@login_required
def ticket_view2(request):
    key = request.GET.get('id')
    try:
        # lookup            = (Ticket.objects.select_related('author').get(id = key))
        lookup            = (Ticket.objects.select_related('author').get(id = key, online = True))
        # if lookup.status != '4':
        #     # if request.is_agent:
        #     if 'chat_id' not in request.session or not request.session['chat_id']:
        #         request.session['chat_id'] = [key]
        #     else:
        #         save_list = request.session['chat_id']
        #         if key not in save_list:
        #             save_list.append(key)
        #         else:
        #             pass
        #         request.session['chat_id'] = save_list
        # else:
        #     del request.session['chat_id']
    except Exception, err:
        # return HttpResponseRedirect(reverse('tickets'))
        return HttpResponse(err)
    return render_to_response('ticket/ticket_detail_new.html', locals(),context_instance=RequestContext(request))



@login_required
def ticket_view1(request):
    key = request.GET.get('id')
    ajax = request.GET.get('ajax')
    try:
        lookup = Ticket.objects.get(id=key)
    except Exception, err:
        return HttpResponseRedirect(reverse('tickets'))
    if ajax == 'True':

        data    =   render_to_string('dashboard/ajax/ticket_detail1.html', locals(), context_instance=RequestContext(request))
        resp    =   { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('ticket/ticket_detail1.html', locals(),context_instance=RequestContext(request))


from service.tasks import mail_notification
@login_required
def ticket_status(request):
    #get user fullname or username
    if len(str(request.user.get_full_name())) > 0:
        get_user = str(request.user.get_full_name())
    else:
        get_user = str(request.user.username)

    if request.method == 'POST':

        key = request.POST.get('id')

        ticket = Ticket.objects.get(id = key)
        if ticket.status != request.POST.get('status'):
            change_status = True
        else:
            change_status = False
        ticket.status = request.POST.get('status')
        if request.POST.get('add_timer'):
            ticket.add_timer_reopen = request.POST.get('add_timer')

        if request.POST.get('status') == '5' and ticket.reopen == 0:
            ticket.reopen = 1
        
        if request.POST.get('comment'):
            message = request.POST.get('comment')
        else:
            if request.POST.get('status') == '1':
                status = 'Open'
            if request.POST.get('status') == '2':
                status = 'Hold'
            if request.POST.get('status') == '3':
                status = 'Resolved'
            if request.POST.get('status') == '4':
                status = 'Close'
            if request.POST.get('status') == '5':
                status = 'Re-Open'
            if request.POST.get('status') == '6':
                status = 'Assigned'
            message = '%s change status to %s' % (get_user, status)

        #send chatbox message if ticket is live:
        if ticket.live == True:
            try:
                data = {"user": str(request.user.get_full_name), "message": message, "id": key, 'change_status':'True'}
                channnel = "room-" + key
                chat_api(data, channnel)
            except Exception, e:
                print(e)

        ticket.live = False

        c = Comment()
        c.user = request.user
        c.text = message
        c.timestamp = datetime.now()
        if change_status:
            c.change_status = True
        try:
            c.attachment = request.FILES['attachment']
        except:
            pass
        d = c.save()
        ticket.comments.add(c)
        ticket.save()

        if ticket.status == '6':
            get_current_time = datetime.now()
            get_ticket_assigned = ticket.timestamp_mod
            get_time = get_ticket_assigned.replace(tzinfo=None) #remove this if settings.TIME_ZONE = None
            count_time = get_current_time - get_time
            get_hour_time = count_time.seconds / 3600 

            try:
                get_time_to_resolve = TimetoResolve.objects.get(ticket = ticket)
            except:
                get_time_to_resolve = TimetoResolve()
                get_time_to_resolve.ticket = ticket
            get_time_to_resolve.time = get_time_to_resolve.time - get_hour_time
            get_time_to_resolve.save()

        time = datetime.now().strftime('%b %d, %Y, %H %p')

        if change_status:
            notif_type = 1
            ref_id = ticket.id
        else:
            notif_type = 2
            ref_id = c.id

        if request.is_agent:
            Notification.objects.create(timestamp = datetime.now(), notif_type = notif_type, to = ticket.author, ref_id = ref_id)
            if notif_type == 1:
                str_message = 'Ticket %s change state' % ref_id
            else:
                str_message = 'New Comment in ticket %s' % ref_id
            mail_notification.delay('Ticket Status', [ticket.author.email], str_message)
            
        else:
            Notification.objects.create(timestamp = datetime.now(), notif_type = notif_type, to = ticket.assigned.user, ref_id = ref_id)
            if notif_type == 1:
                str_message = 'Ticket %s change state' % ref_id
            else:
                str_message = 'New Comment in ticket %s' % ref_id
            mail_notification.delay('Ticket Status', [ticket.author.email], str_message)
            

        resp = {'status': True, 'status':ticket.status, 'id': key, 'msg': message, 'time': time}

        act = Activity()
        act.user = request.user
        act.text = "created new comment on ticket %s" % ticket.title
        act.save()

        return HttpResponse(json.dumps(resp, cls=DjangoJSONEncoder), content_type='application/json')

    else:
        pass


@login_required
def iframe(request):
    try:
        key = request.GET.get('id')
        lookup = Forms.objects.get(id=key)
    except Exception:
        pass

    department_list = request.user.company.departments.all()
    return render_to_response('form_builder/iframe_form.html', locals(), context_instance=RequestContext(request))

@login_required
def iframe_customer(request):
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        try:
            key = request.GET.get('id')
            lookup = Forms.objects.get(id=key)
            if lookup.company.logo == "":
                logo_company = ""
            else:
                logo_company = lookup.company.logo.url
        except Exception:
            pass
        resp = {'status': True, 'data': lookup.form_content, 'logo': logo_company, 'form_name': lookup.name}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('form_builder/iframe_customer.html', locals(), context_instance=RequestContext(request))

@login_required
def verification_mobile(request, val=None):
    return render_to_response('dashboard/verification_mobile.html', context_instance=RequestContext(request))


@csrf_exempt
def api_mobile(request):

    phone_number = request.POST.get('phone_number')
    API_KEY='RA$F73CCDE6-6A3C-11E4-941A-94DE80A5CEAB'
    try:
        email = request.session["activation_email"]
    except:
        pass
    
    #testing
    # response = urllib2.urlopen("http://engine.dial2verify.in/Integ/API.dvf?mobile=9920123456&passkey=RA$63AF2BAE-A1f2-11S2-B32F-36F93F4SCB0G&notify="+request.META.get('HTTP_HOST')+"verification_mobile/&out=JSON&cn=UK")
    
    #ori
    # response = urllib2.urlopen("http://engine.dial2verify.in/Integ/API.dvf?mobile="+phone_number+"&passkey=RA$F73CCDE6-6A3C-11E4-941A-94DE80A5CEAB&notify="+request.META.get('HTTP_HOST')+"verification_mobile/&e-notify="+request.user.email+"&out=JSON&cn=IN")

    #new
    # response = urllib2.urlopen("http://engine.dial2verify.in/Integ/API.dvf?mobile="+phone_number+"&passkey=RA$F73CCDE6-6A3C-11E4-941A-94DE80A5CEAB&notify="+request.META.get('HTTP_HOST')+"verification_mobile/&e-notify="+email+"&out=JSON&cn=IN")
    response = urllib2.urlopen("http://engine.dial2verify.in/Integ/API.dvf?mobile="+phone_number+"&passkey=RA$F73CCDE6-6A3C-11E4-941A-94DE80A5CEAB&notify="+request.META.get('HTTP_HOST')+"verification_mobile/&out=JSON&cn=IN")
    
    data = json.load(response)
    djson_data=response.read()
    try:
        request.session['sid'] = data["SessionId"]
    except Exception, e:
        # print(e)
        pass
        # return HttpResponse(data)

    return HttpResponse(json.dumps(data), content_type='application/json')


@csrf_exempt
def verify_status(request):
    
    SID = request.session["sid"]
    # email = request.session['activation_email']
    # SID = 'RA$6DA28635-7536-11E4-941A-94DE80A5CEAB' #testing verified status
    # SID = 'RA$A8361286-753D-11E4-941A-94DE80A5CEAB' #testing unverified status

    response=urllib2.urlopen("http://engine.dial2verify.in/Integ/UserLayer/DataFeed_APIV2.dvf?SID=%s" % SID)
    data = json.load(response)
    phone = data["VerifiedMobileNumber"]
    # return HttpResponse(data["VerifiedMobileNumber"])

    if data["VerificationStatus"] == 'VERIFIED':
        try:
            a = User.objects.get(customer__mobile_number = phone)
            a.is_active = True
            a.save()
            d = Customer.objects.get(user = a)
            d.mobile_verified = True
            d.save()
        except:
            a = User.objects.get(company__phone = phone)
            a.is_active = True
            a.save()
            d = Company.objects.get(user = a)
            d.phone_verified = True
            d.save()

    return HttpResponse(json.dumps(data), content_type='application/json')




@login_required
def chat(request):
    key = request.GET.get('id')
    lookup = Ticket.objects.get(id=key)

    return render_to_response('chat/chat.html', locals(), context_instance=RequestContext(request))

@login_required
def response(request):

    if request.method == "POST":
        try:
            room = request.POST.get('id')
            data = {"action": "system", "message": request.POST["text"]}
            broadcast_channel(data, channel="room-" + room)

            t = Ticket.objects.get(id=1)
            c = Comment()
            c.user = request.user
            c.text = request.POST["text"]
            c.timestamp = datetime.now()
            c.save()
            t.comments.add(c)
            t.save()
            i = c
        except Exception, err:
            pass
            print(err)

    return HttpResponse('ok')


@login_required
def service_provider(request):
    len_provider = len(ServiceProvider.objects.filter(user = request.user))
    total_reject = ServiceProvider.objects.filter(status=2,user=request.user).count()
    total_verified = ServiceProvider.objects.filter(status=1,user=request.user).count()
    total_need_verified = ServiceProvider.objects.filter(status=0,user=request.user).count()
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        # return render_to_response('dashboard/ajax/service_provider.html', locals(), context_instance=RequestContext(request))
        data    = render_to_string('dashboard/ajax/service_provider.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/service_provider.html', locals(), context_instance=RequestContext(request))

@login_required
def lookup_service_provider(request):
    service_providers = ServiceProvider.objects.filter(user = request.user)
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        return render_to_response('dashboard/ajax/lookup_service_provider.html', locals(), context_instance=RequestContext(request))
    else:
        return render_to_response('dashboard/lookup_service_provider.html', locals(), context_instance=RequestContext(request))    


# from dashboard.forms import ServiceProviderForm
@login_required
def add_new_provider(request):
    # form = ServiceProviderForm()
    from_forms = request.GET.get('from')
    value_select_form = request.GET.get('value_select_form')
    if request.method == 'POST':
        company                         = Company.objects.get(id = request.POST.get('company'))
        product                         = Department.objects.get(id = request.POST.get('product'))
        account_number                  = request.POST.get('acount_number')
        registered_mobile_number        = request.POST.get('registered_mobile_number')
        dob                             = request.POST.get('dob')
        mothers                         = request.POST.get('mothers')
        value_form                      = request.POST.get('from_form')
        value_select                    = request.POST.get('value_select')

        #cek_mobile
        try:
            cek_mobile = Customer.objects.get(mobile_number = registered_mobile_number)
            try:
                a = ServiceProvider(user = request.user, company = company, product = product, account_number = account_number, 
                registered_mobile_number = registered_mobile_number, dob = dob, mothers_name = mothers, status = "0")
                a.save()

                act = Activity()
                act.user = request.user
                act.text = "created new service provider"
                act.save()

                if request.is_ajax():
                    if value_form:
                        resp = {'status': 'True', 'msg': 'Success', 'next_url': value_form, 'company': request.POST.get('company'), 'department': request.POST.get('product'), 'value_select_form': value_select }
                    else:
                        resp = {'status': 'True', 'msg': 'Success', 'next_url': '' }
                else:
                    if value_form:
                        resp = {'status': 'True', 'msg': 'Success', 'next_url': value_form, 'company': request.POST.get('company'), 'department': request.POST.get('product'), 'value_select_form': value_select }
                    else:
                        # return HttpResponseRedirect('/dashboard/my-service-providers/')
                        resp = {'status': 'True', 'msg': 'Success', 'next_url': '' }
            except Exception, e:
                if request.is_ajax():
                    resp = {'status': 'False', 'msg': 'error'}
                else:
                    return HttpResponse(e)
        except Exception, e:
            resp = {'status': 'False', 'msg': 'Registered Mobile Number Not Found'}

        return HttpResponse(json.dumps(resp), content_type='application/json')

    if request.GET.get('company'):
        data_copy_company = Company.objects.get(id=request.GET.get('company'))
        data_copy_product = request.GET.get('department')
    
    company = Company.objects.filter(user__is_active = True, email_verified = True, phone_verified = True)
    ajax = request.GET.get('ajax')
    if ajax == 'True':
        # return render_to_response('dashboard/ajax/new_service_provider.html', locals(), context_instance=RequestContext(request))
        data    = render_to_string('dashboard/ajax/new_service_provider.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('dashboard/new_service_provider.html', locals(), context_instance=RequestContext(request))

@login_required
def delete_service_provider(request):
    resp = { 'status': False, 'msg': 'Bad request' }
    if request.POST:
        service_id = request.POST.get('id')
        try:
            service_providers = ServiceProvider.objects.get(user = request.user, id=service_id)
            service_providers.delete()

            act = Activity()
            act.user = request.user
            act.text = "deleted service provider"
            act.save()

            resp = { 'status': True, 'msg': 'Successfully delete request service provider' }
        except Exception, e:
            resp = { 'status': False, 'msg': unicode(e) }
        
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def add_again_service_provider(request):
    # resp = { 'status': False, 'msg': 'Bad request' }
    if request.POST:
        service_id = request.POST.get('id')
        try:
            service_providers = ServiceProvider.objects.get(user = request.user, id=service_id)

            company                         = service_providers.company
            product                         = service_providers.product
            account_number                  = service_providers.account_number
            registered_mobile_number        = service_providers.registered_mobile_number
            dob                             = service_providers.dob
            mothers                         = service_providers.mothers_name

            try:
                cek_mobile = Customer.objects.get(mobile_number = registered_mobile_number)
            except Exception, e:
                resp = {'status': False, 'msg': 'Registered Mobile Number Not Found'}
            else:
                sp_except_reject = ServiceProvider.objects.filter(company = company, product = product, user = request.user).exclude(status="2")

                if sp_except_reject:
                    resp = {'status': False, 'msg': 'Request service provider already added'}                    
                else:
                    try:
                        a = ServiceProvider(user = request.user, company = company, product = product, account_number = account_number, 
                        registered_mobile_number = registered_mobile_number, dob = dob, mothers_name = mothers, status = "0")
                        a.save()

                        act = Activity()
                        act.user = request.user
                        act.text = "created service provider"
                        act.save()
                        if request.is_ajax():
                            resp = {'status': True, 'msg': 'Success'}
                        else:
                            return HttpResponseRedirect('/dashboard/my-service-providers/')
                    except Exception, e:
                        resp = {'status': False, 'msg': 'error'}
        except Exception, e:
            resp = { 'status': False, 'msg': unicode(e) }

    id_service = request.GET.get('id') 
    data_copy = ServiceProvider.objects.get(user = request.user, id=id_service)

    data_copy_company                         = data_copy.company
    data_copy_product                         = data_copy.product
    data_copy_account_number                  = data_copy.account_number
    data_copy_registered_mobile_number        = data_copy.registered_mobile_number
    data_copy_dob                             = data_copy.dob
    data_copy_mothers                         = data_copy.mothers_name

    company = Company.objects.filter(user__is_active = True, email_verified = True, phone_verified = True)
    return render_to_response('dashboard/ajax/new_service_provider.html', locals(), context_instance=RequestContext(request))
    # return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required
def get_subscribe_provider(request):
    company     = request.GET.get('company')
    department  = request.GET.get('department')
    try:
        get_company = Company.objects.get(id = company)
        department = Department.objects.get(id = department)
        # department_list = ServiceProvider.objects.filter(company = get_company, product = department, user = request.user).exclude(status="2")

        # if department_list.status == "2":
        #     return HttpResponse('True')
        # else:
        #     return HttpResponse('False')
    except Exception, e:
        return HttpResponse('False')
    else:
        department_lists = ServiceProvider.objects.filter(company = get_company, product = department, user = request.user).exclude(status="2")

        if len(department_lists) == 0:
            return HttpResponse('False')
        else:
            return HttpResponse('True')


@login_required
def verified_subscribe_provider(request):
    resp = {'status': False, 'msg': 'Bad Request'}
    if request.POST and request.is_ajax():
        try:
            get_service = ServiceProvider.objects.get(id = request.POST.get('key'))
            get_service.status = request.POST.get('val')
            get_service.reason = request.POST.get('reason')
            get_service.save()
        except Exception, err:
            resp = {'status': False, 'msg': unicode(err)}
        else:
            if request.POST.get('val') == "1":
                act = Activity()
                act.user = request.user
                act.text = "approved service providers"
                act.save()
            elif request.POST.get('val') == "2":
                act = Activity()
                act.user = request.user
                act.text = "rejected service providers"
                act.save()

            resp = {'status': True, 'msg': 'success'}
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def kyc_partner(request):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if request.is_kyc:
        q = KYCInformation.objects.filter(status = False)
        if request.method == 'POST':
            get_kyc                         = KYCInformation.objects.get(id = request.POST.get('id'))
            get_kyc.authorized_name         = request.POST.get('name')
            get_kyc.authorized_signature    = request.FILES.get('signature')
            get_kyc.date_authorized         = request.POST.get('date')
            get_kyc.employee_number         = request.POST.get('employee_number')
            get_kyc.authorized_seal         = request.FILES.get('authorized_seal') 
            get_kyc.status                  = request.POST.get('status')
            get_kyc.save()
            return HttpResponseRedirect('/dashboard/kyc-partner/')
        return render_to_response('kyc/kyc_partner_dashboard.html', locals(), context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/dashboard')


@login_required
def my_kyc_verification(request):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if request.is_kyc:
        len_kyc = len(KYCInformation.objects.all())
        q = KYCInformation.objects.filter(status = False)
        if request.method == 'POST':
            get_kyc                         = KYCInformation.objects.get(id = request.POST.get('id'))
            get_kyc.authorized_name         = request.POST.get('name')
            get_kyc.authorized_signature    = request.FILES.get('signature')
            get_kyc.date_authorized         = request.POST.get('date')
            get_kyc.employee_number         = request.POST.get('employee_number')
            get_kyc.authorized_seal         = request.FILES.get('authorized_seal') 
            get_kyc.status                  = request.POST.get('status')
            get_kyc.save()
            return HttpResponseRedirect('/dashboard/kyc-partner/')
        return render_to_response('kyc/my_kyc_verification.html', locals(), context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/dashboard')



@login_required
def agent_view_forms(request):
    department = request.user.agent.department
    company = request.user.agent.get_company
    ajax = request.GET.get('ajax')
    if ajax == "True":
        # return render_to_response('dashboard/ajax/view_forms.html', locals(), RequestContext(request))
        data    = render_to_string('dashboard/ajax/view_forms.html', locals(), context_instance=RequestContext(request))
        resp    = { 'status': True, 'msg': data }
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return render_to_response('agent/view_forms.html', locals(), RequestContext(request))



@login_required
def company_settings(request):
    if request.is_company:
        #check company setting if exist
        try:
            check_setting = CompanySettings.objects.get(company__user__username = request.user.username)
            if request.method == 'POST':
                form = CompanySettingForm(request.POST, instance = check_setting)
                if form.is_valid():
                    form.save()

            else:
                form = CompanySettingForm(instance = check_setting)


        except Exception, e: # if company doesn't exist create new one
            if request.method == 'POST':
                form = CompanySettingForm(request.POST)
                if form.is_valid():
                    save_form = form.save(commit = False)
                    save_form.company = request.user.company
                    save_form.save()

            else:
                form = CompanySettingForm()

    else:
        return HttpResponseRedirect('/')

    return render_to_response('dashboard/settings.html', locals(), RequestContext(request))
