from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.template.defaultfilters import slugify

from django.db.models import Q, Min, Max, Sum, Avg, Count
from django.utils.safestring import mark_safe
from encrypted_fields import *
from datetime import date, datetime, timedelta
from django_countries.fields import CountryField

from datetime import *

# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User)
    mobile_number = models.CharField(max_length=20)
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=50, null=True, blank=True)
    mobile_verified = models.BooleanField(default=False)
    mobile_verification_code = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photo', null=True, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

class Feature(models.Model):
    title = models.CharField(max_length=100)
    order_num = models.IntegerField(default=1)

    def __unicode__(self):
        return '%s' % self.title


class Plan(models.Model):
    name = models.CharField(max_length=50)
    price = models.FloatField(default=0.0)
    features = models.ManyToManyField(Feature, null=True, blank=True)
    order_num = models.IntegerField(default=1)
    limit_agent = models.CharField(max_length=50, null=True, blank=True)
    limit_department_head = models.CharField(max_length=50, null=True, blank=True)
    limit_department = models.CharField(max_length=50, null=True, blank=True)
    limit_form = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        return '%s' % self.name

    def feature_list(self):
        result = ''
        for i in self.features.all().order_by('order_num'):
            result += '%s. %s<br>' % (i.order_num, i.title)

        if not result:
            result = '-'
        return mark_safe(result)

class SiteData(models.Model):

    STATUS_CHOICE = (
        ('Trial', 'Trial'),
        ('Approved', 'Approved'),
        ('Change', 'Change'),
    )

    SUBSCRIPTION_CHOICE = (
        ('1 Month', '1 Month'),
        ('3 Months', '3 Months'),
        ('6 Months', '6 Months'),
        ('12 Months', '12 Months'),
    )

    name = models.CharField(max_length=100)
    expired = models.DateField(null=True, blank=True)
    plan = models.ForeignKey(Plan, null=True, blank=True)
    subscription = models.CharField(max_length=100, null=True, blank=True, choices = SUBSCRIPTION_CHOICE)
    status = models.CharField(max_length=100, null=True, blank=True, default="Trial", choices = STATUS_CHOICE)
    request_plan = models.CharField(max_length=100, null=True, blank=True)
    subscribe_plan = models.CharField(max_length=100, null=True, blank=True, choices = SUBSCRIPTION_CHOICE)
    company = models.ForeignKey('Company')

    def __unicode__(self):
        return '%s' % self.name

    def save(self, *args, **kwargs):
        default_date = 30
        if self.status == "Approved":
            subscribe_plan_split = int(self.subscribe_plan.split()[0])
            request_plan = mark_safe(self.request_plan)
            p = Plan.objects.get(name=request_plan)
            self.plan = p
            self.expired = date.today() + timedelta(default_date * subscribe_plan_split)
            self.request_plan = ""
            self.subscription = self.subscribe_plan
            self.subscribe_plan = ""
            c = Company.objects.get(id=self.company_id)
            c.is_trial = False
            c.save()
            
        super(SiteData, self).save(*args, **kwargs)

class HeadCompany(models.Model):
    user = models.OneToOneField(User, related_name='head_company')
    departments = models.ManyToManyField('Department', null=True, blank=True)
    photo = models.ImageField(upload_to='photo', null=True, blank=True)
    phone = models.CharField(max_length=50, null=True)
    address = models.TextField(null=True, blank=True)

    def agents(self):
        result = []
        for i in self.departments.all():
            result += list(i.get_agents())
        return result

    def agents_request(self):
        result = []
        for i in self.departments.all():
            result += list(i.get_agents_request())
        return result

    def get_tickets(self):
        return Ticket.objects.filter(department__in=[i.id for i in self.departments.all()])

    def __unicode__(self):
        return '%s' % self.id

class CategoryCompany(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)

    def __unicode__(self):
        return '%s' % self.name

class Company(models.Model):
    user = models.OneToOneField(User)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='logo', null=True, blank=True)
    company_name = models.CharField(max_length=100)
    about_us = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True)
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=50, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    departments = models.ManyToManyField('Department', null=True, blank=True)
    heads = models.ManyToManyField(HeadCompany, null=True, blank=True, related_name='heads_company')
    is_trial = models.BooleanField(default=True)
    category_company = models.ForeignKey(CategoryCompany, null=True)

# maybe have others field here later
    def __unicode__(self):
        return '%s' % self.company_name

    def domain(self):
        try:
            result = SiteData.objects.get(company=self)
        except Exception:
            result = None
        return result

    def expired(self):
        try:
            result = SiteData.objects.get(company=self).expired
        except Exception:
            result = None
        return result


    def save(self, *args, **kwargs):
        super(Company, self).save(*args, **kwargs)
        try:
            d = SiteData.objects.get(company=self)
        except Exception:
            d = SiteData()
            d.name = slugify(self.company_name)
            d.expired = date.today() + timedelta(days=1)
            d.company = self
            d.save()

    def agents(self):
        result = []
        for i in self.departments.all():
            result += list(i.get_agents())
        return result

    def agents_request(self):
        result = []
        for i in self.departments.all():
            result += list(i.get_agents_request())
        return result

    def forms(self):
        return Forms.objects.filter(company=self)

    def service_providers(self):
        return ServiceProvider.objects.filter(company=self)


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def get_agents(self):
        return Agent.objects.filter(department=self)

    def get_agents_request(self):
        return AgentRequest.objects.filter(department=self)

    def get_heads(self):
        return HeadCompany.objects.filter(departments=self)

    def get_head(self):
        return HeadCompany.objects.get(departments=self)

    def agent_list(self):
        result = ''
        for i in Agent.objects.filter(department=self):
            result += '- %s %s<br>' % (i.user.first_name, i.user.last_name)

        if not result:
            result = '-'
        return mark_safe(result)

    def escalated_tickets(self):
        return Ticket.objects.filter(status='2', department=self).count()

    def total_tickets_resolved(self):
        return Ticket.objects.filter(status='3', department=self).count()

    def total_tickets_assigned(self):
        return Ticket.objects.filter(status='6', department=self).count()

    def total_tickets_assigned_today(self):
        return Ticket.objects.filter(status='6', department=self, timestamp_mod=datetime.now().date()).count()

    def total_tickets_resolved_today(self):
        return Ticket.objects.filter(status='3', department=self, timestamp_mod=datetime.now().date()).count()

    def escalated_tickets_today(self):
        return Ticket.objects.filter(status='2', department=self, timestamp_mod=datetime.now().date()).count()

    def total_tickets_assigned_month(self):
        return Ticket.objects.filter(status='6', department=self, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()

    def total_tickets_resolved_month(self):
        return Ticket.objects.filter(status='3', department=self, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()

    def escalated_tickets_month(self):
        return Ticket.objects.filter(status='2', department=self, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()

    def total_tickets_assigned_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        return Ticket.objects.filter(status='6', department=self, timestamp_mod__range=[start_week, end_week]).count()

    def total_tickets_resolved_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        return Ticket.objects.filter(status='3', department=self, timestamp_mod__range=[start_week, end_week]).count()

    def escalated_tickets_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        return Ticket.objects.filter(status='2', department=self, timestamp_mod__range=[start_week, end_week]).count()

    def __unicode__(self):
        return '%s' % self.name

class AgentRequest(models.Model):
    APPROVAL_STATUS = (
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Decline'),
        (3, 'Removed'),
        (4, 'Edited'),
    )

    agent = models.ForeignKey('Agent', null=True, blank=True)
    department = models.ForeignKey(Department, null=True)
    email = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, null=True)
    address = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photo', null=True, blank=True)
    status = models.IntegerField(default=0, choices=APPROVAL_STATUS)

    def __unicode__(self):
        return unicode(self.id)

    def status_(self):
        return self.APPROVAL_STATUS[self.status][1]

    def get_company(self):
        return self.department.company_set.get()

    def get_mail_company(self):
        return self.get_company().user.email

    def get_mail_head(self):
        return self.department.get_head().user.email

class Agent(models.Model):

    STATUS_CHOICE = (
        ('1', 'Away'),
        ('2', 'On Leave'),
    )

    department = models.ForeignKey(Department, null=True)
    user = models.OneToOneField(User, related_name='agent')
    phone = models.CharField(max_length=50, verbose_name='Mobile Phone')
    address = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='photo', null=True, blank=True)
    is_online = models.BooleanField(default = False) #if online True else False
    active_chat = models.IntegerField(default = 0)
    status = models.CharField(max_length=2, choices=STATUS_CHOICE, null=True, blank=True)
    day_on_leave = models.CharField(max_length=20, null=True, blank=True)
    date_start_leave = models.DateField(null=True, blank=True)
    request_remove = models.BooleanField(default=False)

    def get_company(self):
        try:
            result = Company.objects.get(departments__in=[self.department])
        except Exception:
            result = None
        return result

    def save(self, *args, **kwargs):
        if self.status == '2':
            if self.date_start_leave == None:
                self.date_start_leave = date.today() + timedelta(int(self.day_on_leave))
                self.is_online = False
            else:
                if date.today() > self.date_start_leave + timedelta(int(self.day_on_leave)):
                    self.status = None
                    self.day_on_leave = ""
                    self.date_start_leave = None
                    self.is_online = True
                else:
                    self.is_online = False
        elif self.status == '1':
            self.is_online = True
            self.day_on_leave = ""
            self.date_start_leave = None
        super(Agent, self).save(*args, **kwargs)

    def total_assigned(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(assigned__in=assigned_user, status__in=['6', '2']).count()
        except Exception:
            result = 0
        return result

    def total_resolved_ticket(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(assigned__in=assigned_user, status=3).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_assigned_today(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='6', assigned__in=assigned_user, timestamp_mod=datetime.now().date()).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_resolved_today(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='3', assigned__in=assigned_user, timestamp_mod=datetime.now().date()).count()
        except Exception, e:
            result = 0

        return result

    def escalated_tickets_today(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='2', assigned__in=assigned_user, timestamp_mod=datetime.now().date()).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_assigned_month(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='6', assigned__in=assigned_user, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_resolved_month(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='3', assigned__in=assigned_user, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()
        except Exception, e:
            result = 0

        return result

    def escalated_tickets_month(self):
        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='2', assigned__in=assigned_user, timestamp_mod__month=datetime.now().month, timestamp_mod__year=datetime.now().year).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_assigned_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='6', assigned__in=assigned_user, timestamp_mod__range=[start_week, end_week]).count()
        except Exception, e:
            result = 0

        return result

    def total_tickets_resolved_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='3', assigned__in=assigned_user, timestamp_mod__range=[start_week, end_week]).count()
        except Exception, e:
            result = 0

        return result

    def escalated_tickets_week(self):
        date = datetime.now().today()
        start_week = date - timedelta(date.weekday())
        end_week = start_week + timedelta(7)

        try:
            assigned_user = AssignedUser.objects.values_list('id', flat=True).filter(user=self.user)
            result = Ticket.objects.filter(status='2', assigned__in=assigned_user, timestamp_mod__range=[start_week, end_week]).count()
        except Exception, e:
            result = 0

        return result

    def __unicode__(self):
        return '%s' % self.user

class Comment(models.Model):
    user = models.ForeignKey(User)
    text = models.TextField(blank = True, null = True)
    change_status = models.BooleanField(default = False)
    timestamp = models.DateTimeField()
    timestamp_mod = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachment',null=True, blank=True)

    def __unicode__(self):
        return '%s' % self.text

class AssignedUser(models.Model):
    user = models.ForeignKey(User)
    leave = models.NullBooleanField(default=False, null=True, blank=True)
    leave_reason = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    timestamp_mod = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s' % self.user.username


class Ticket(models.Model):

    # STATUS_CHOICE = (
    #     ('1', 'Open'),
    #     ('2', 'Hold'),
    #     ('3', 'Resolved'),
    #     ('4', 'Close'),
    #     ('5', 'Re-Open'),
    #     ('6', 'Assigned'),
    # )
    STATUS_CHOICE = (
        ('6', 'Assigned'),
        ('2', 'On-Hold'),
        ('5', 'Re-Open'),
        ('3', 'Resolved'),
        ('4', 'Close'),
        ('1', 'Open'),
    )

    author = models.ForeignKey(User, null=True, blank=True, related_name='author')
    department = models.ForeignKey(Department, null=True, blank=True, related_name='department')
    assigned = models.ForeignKey(AssignedUser, null=True, blank=True)

    live = models.BooleanField(default=False) # ini status ticket off atau online
    online = models.BooleanField(default=False) # ini status ticket on chat or not

    title = models.CharField(max_length=200)
    timestamp = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    comments = models.ManyToManyField('Comment', null=True, blank=True)
    timestamp_mod = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, default='1', choices = STATUS_CHOICE)
    feedback = models.NullBooleanField(null=True, blank=True)
    timeout = models.IntegerField(default=48) # in hours
    reopen = models.IntegerField(default=0)
    add_timer_reopen = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s' % self.title


    def is_live(self): # ini status author on atau off
        one_hour_ago = datetime.now() - timedelta(hours=1)
        sql_datetime = datetime.strftime(one_hour_ago, '%Y-%m-%d %H:%M:%S')
        cek = Ticket.objects.filter(author__last_login__gt=sql_datetime, assigned__user__last_login__gt=sql_datetime, id=self.id)
        if len(cek) > 0:
            return True
        else:
            return False

    # def save(self, *args, **kwargs):
    #     if self.live == False and self.assigned == None:
    #         # AssignedUser.objects.values('user__username').annotate(totals=Count('user')).order_by('totals')
    #         agents = Agent.objects.filter(department=self.department)
    #         data_array = []
    #         data_dict = dict()

    #         for i in agents:
    #             data_dict['user'] = i.user.id
    #             data_dict['totals'] = i.total_assigned
    #             data_array.append(data_dict)
    #             data_dict = dict()

    #         data_lowest = sorted(data_array)[0]
    #         user = User.objects.get(id=data_lowest['user'])
    #         assigned = AssignedUser.objects.create(user = user, timestamp = datetime.now())
    #         self.assigned = assigned
    #         self.status = '6'
    #     super(Ticket, self).save(*args, **kwargs)

class TimetoResolve(models.Model):
    ticket = models.ForeignKey(Ticket)
    time = models.IntegerField(default = 0)
    due = models.DateTimeField(blank = True, null = True)

    def __unicode__(self):
        return '%s hours' % self.time

class Notification(models.Model):
    NOTIF_TYPE = (
        (1, 'ticket'),
        (2, 'comment'),
        (3, 'request new agent'),
    )
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField()
    notif_type = models.IntegerField(choices=NOTIF_TYPE)
    to = models.ForeignKey(User)
    ref_id = models.IntegerField()

    def __unicode__(self):
        return '%s' % self.id

    def data(self):
        result = None
        if self.notif_type == 1:
            try:
                result = Ticket.objects.get(id=self.ref_id)
            except Exception:
                pass
        if self.notif_type == 2:
            try:
                result = Comment.objects.get(id=self.ref_id)
            except Exception:
                pass
        if self.notif_type == 3:
            try:
                result = AgentRequest.objects.get(id=self.ref_id)
            except Exception:
                pass
        return result

class FileFormCustomer(models.Model):
    label_file = models.CharField(max_length=200, null=True, blank=True)
    file_name = models.FileField(upload_to='file_customer', null=True, blank=True)

    def __unicode__(self):
        return '%s' % (self.label_file)

    def name_label(self):
        msg = '%s' % (self.label_file)
        return mark_safe(msg)

    def file(self):
        result = ''
        if self.file_name:
            # result += '<img src="%s" style="width:200px;" />' % self.file_name.url
            result += '%s' % (self.file_name.name)
        else:
            result = '-'
        if not result:
            result = '-'
        return mark_safe(result)

class FormCustomer(models.Model):
    user = models.ForeignKey(User)
    form_value = models.TextField()
    # file_form = models.FileField(upload_to='file_customer', null=True, blank=True)
    file_form_customers = models.ManyToManyField(FileFormCustomer, null=True, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def name_user(self):
        msg = '%s %s' % (self.user.first_name, self.user.last_name)
        return mark_safe(msg)

    # def file(self):
    #     result = ''
    #     if self.file_form:
    #         result += '<img src="%s" style="width:200px;" />' % self.file_form.url
    #     else:
    #         result = '-'
    #     if not result:
    #         result = '-'
    #     return mark_safe(result)


class Forms(models.Model):

    TYPE_FORM_CHOICE = (
        ('service_request_form','Service Request Form'),
        ('application_form','Application Form'),
        ('query_form','Query Form'),
    )

    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company)
    department = models.ForeignKey(Department, null=True)
    form_content = models.TextField()
    type_form = models.CharField(max_length=255, null=True, choices=TYPE_FORM_CHOICE)
    form_customers = models.ManyToManyField('FormCustomer', null=True, blank=True)

    def __unicode__(self):
        return '%s' % self.name



class KYCPartner(models.Model):
    user = models.OneToOneField(User)
    email = models.EmailField(max_length=70)
    mobile = models.CharField(max_length = 50, verbose_name = 'Mobile Phone')
    first_name = models.CharField(max_length = 50, null = True, blank = True)
    last_name = models.CharField(max_length = 50, null = True, blank = True)
    dob = models.DateField(blank = True, null = True)
    address = models.TextField(blank = True, null = True)
    complete_data = models.BooleanField(default = False)

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)


class KYCInformation(models.Model):

    GENDER_CHOICE = (
        ('M', 'Male'),
        ('F', 'Female')
    )

    IS_PERMANENT_ADDRESS = (
        ('1', 'Same as Current Residence Address'),
        ('2', 'No')
    )

    MARITAL_CHOICE = (
        ('single', 'Single'),
        ('married', 'Married')
    )

    STATUS_CHOICE = (
        ('1', 'Resident Individual'),
        ('2', 'Non Resident'),
        ('3', 'Foreign National (Passport Copy Mandatory for NRIs & Foreign National)')
    )

    PROFF_IDENTITY_CHOICE = (
        ('1', 'Aadhaar Number'),
        ('2', 'Passport'),
        ('3', 'Voter ID'),
        ('4', 'Driving License'),
        ('5', 'Others')
    )

    PROOF_ADDRESS_CHOICE = (
        ('1', 'Passport'),
        ('2', 'Ration Card'),
        ('3', 'Registered Lease/Sale Agreement of Residence'),
        ('4', 'Driving License'),
        ('5', 'Voter Identity Card'),
    )

    GROSS_ANNUAL_INCOME_DETAIL = (
        ('1', 'Below 1 Lac'),
        ('1', '1-5 Lac'),
        ('1', '5-10 Lac'),
        ('1', '10-25 Lac'),
        ('1', '> 25 Lac')
    )

    OCCUPATION_CHOICE = (
        ('1', 'Private Sector Service'),
        ('2', 'Public Sector'),
        ('3', 'Government Service'),
        ('4', 'Business'),
        ('5', 'Professional'),
        ('6', 'Agriculturist'),
        ('7', 'Retired'),
        ('8', 'Housewife'),
        ('9', 'Student'),
        ('10', 'Forex Dealer'),
        ('11', 'Others'),
    )

    user                                = models.OneToOneField(User)
    photograph                          = models.ImageField(upload_to = 'kyc/', help_text = 'Please upload your recent {X x Y Size} Photograph (supported format - .jpg, jpeg or png)')
    status                              = models.BooleanField(default = False)
    # name                                = models.CharField(max_length = 100, verbose_name='Name of Applicant', help_text = 'As appearing in supporting identification document')
    first_name                          = models.CharField(max_length = 100)
    middle_name                         = models.CharField(max_length = 100, blank = True, null = True)
    last_name                           = models.CharField(max_length = 100)
    father_name                         = models.CharField(max_length = 100, verbose_name='Father/Spouse Name')
    gender                              = models.CharField(max_length = 1, choices = GENDER_CHOICE)
    marital_status                      = models.CharField(max_length = 10, choices = MARITAL_CHOICE)
    dob                                 = models.DateField(help_text = 'dd/mm/yyyy', verbose_name = 'DOB')
    nationality                         = CountryField()
    pan_card                            = models.CharField(max_length = 10, verbose_name = 'PAN Card Number', help_text = 'Please enclose a dully attested copy of you PAN Card', null = True, blank = True)
    pan_card_file                       = models.FileField(upload_to = 'kyc_pan_file/', blank = True, null = True, help_text = "Upload PAN Documents: (supported format - .jpg, pdf or png))")

    residence_status                    = models.CharField(max_length=2, choices=STATUS_CHOICE)
    residence_pasport                   = models.FileField(upload_to = 'kyc_passport', blank = True, null = True, verbose_name = 'Passport or other Documents', help_text = '(supported format - .jpg, png or pdf)')
    residence_address                   = models.CharField(max_length = 100, blank = True, null = True)
    residence_address_city              = models.CharField(max_length = 100, blank = True, null = True, verbose_name = 'City')
    residence_address_pin_code          = models.CharField(max_length = 50, blank = True, null = True, verbose_name = 'PIN Code')
    residence_address_state             = models.CharField(max_length = 100, blank = True, null = True, verbose_name = 'State')
    residence_address_country           = CountryField(verbose_name = 'Country')

    contact_details                     = models.TextField()

    proff_identity                      = models.CharField(max_length = 1, choices = PROFF_IDENTITY_CHOICE, verbose_name = 'Proof of Identity submitted for PAN exempt cases', null = True, blank = True)
    proff_identity_code                 = models.CharField(max_length = 100, blank = True, null = True)

    proff_identity_file                 = models.FileField(upload_to = 'proff_identity_file/', blank = True, null = True)

    #address details
    is_permanent_address                = models.CharField(max_length = 1, choices = IS_PERMANENT_ADDRESS, default = '2')
    permanent_address                   = models.TextField(blank = True, null = True, help_text = "if different from above or overseas address, mandatory for Non-Resident Applicant")

    address_submitted_for_residence     = models.CharField(max_length = 1, choices = PROFF_IDENTITY_CHOICE, verbose_name = "Specify the proof of address submitted for residence address")
    address_submitted_for_residece_file = models.FileField(upload_to = 'address_submit_file/', verbose_name = 'Upload Proof Address Documents')

    proof_of_address_non_residence      = models.CharField(max_length=25, choices=PROOF_ADDRESS_CHOICE, blank = True, null = True)
    proof_of_address_non_residence_file = models.FileField(upload_to = 'proof_of_address_non_residence/', blank = True, null = True)

    signature                           = models.ImageField(upload_to = 'signature/', verbose_name = 'Upload Your Signature Image', help_text="supported format - .jpg")
    date                                = models.DateField(auto_now_add = True, blank = True, null = True)
    date.editable                       = True

    gross_annual_income_detail          = models.CharField(max_length = 1, choices = GROSS_ANNUAL_INCOME_DETAIL, blank = True, null = True)
    net_worth_in                        = models.CharField(max_length = 100, blank = True, null = True)
    net_word_date                       = models.DateField(blank = True, null = True, help_text = "as on (date)")
    occupation                          = models.CharField(max_length = 2, choices = OCCUPATION_CHOICE, blank = True, null = True)
    other_occupation                    = models.CharField(max_length = 50, blank = True, null = True)

    #extra field
    authorized_name                     = models.CharField(max_length = 50, blank = True, null = True, verbose_name = 'Name Authorized Signature')
    authorized_signature                = models.ImageField(upload_to = 'kyc/', blank = True, null = True, verbose_name = 'Authorized Signatory')
    date_authorized                     = models.DateField(blank = True, null = True)
    employee_number                     = models.CharField(max_length = 50, blank = True, null = True)
    authorized_seal                     = models.ImageField(upload_to = 'kyc/', blank = True, null = True)

    share_to                            = models.ManyToManyField(Department, blank = True, null = True)



class KYCInstruction(models.Model):
    instruction = models.TextField()


class ServiceProvider(models.Model):

    STATUS_CHOICE = (
        ("0", "Verification in Progress"),
        ("1", "Approved"),
        ("2", "Rejected"),
    )

    user = models.ForeignKey(User)
    company = models.ForeignKey(Company)
    product = models.ForeignKey(Department, verbose_name = 'Product')
    account_number = models.CharField(max_length = 100)
    registered_mobile_number = models.CharField(max_length = 100)
    dob = models.DateField()
    mothers_name = models.CharField(max_length = 100)
    status = models.CharField(max_length = 1, choices = STATUS_CHOICE, blank = True, null = True)
    reason = models.TextField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s-%s' % (self.company, self.product)

class BrandValue(models.Model):
    company = models.ForeignKey(Company)
    department = models.ForeignKey(Department)
    received_praise = models.CharField(max_length=100, blank = True, null = True)
    negative_feedback = models.CharField(max_length=100, blank = True, null = True)
    total_issue_resolved = models.CharField(max_length=100, blank = True, null = True)
    no_feedback_received = models.CharField(max_length=100, blank = True, null = True)
    extra_less_time_taken = models.CharField(max_length=100, blank = True, null = True)

    def __unicode__(self):
        return '%s-%s' % (self.company.company_name, self.department.name)

class Activity(models.Model):
    user = models.ForeignKey(User)
    text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)


class CompanySettings(models.Model):
    company = models.OneToOneField(Company)
    kyc_mandatory = models.BooleanField(default = False)
    live_chat = models.BooleanField(default = False, verbose_name = 'Live Chat Allowed for Non Customers')
    time_to_resolve = models.IntegerField(default = 96)

class EscalatedTicket(models.Model):
    department = models.ForeignKey(Department)
    ticket = models.ForeignKey(Ticket)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.department)
