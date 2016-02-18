from django.contrib import admin
from models import *

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'mobile_verified', 'email_verified')
    ordering = ['user', 'mobile_number', 'mobile_verified', 'email_verified']
    search_fields = ['user__username', 'user__first_name']

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'domain', 'user', 'phone', 'address', 'email_verified', 'is_trial', 'expired')
    ordering = ['company_name', 'user', 'phone', 'address', 'email_verified']
    search_fields = ['company_name', 'user__username', 'phone', 'address']
    filter_horizontal = ('departments', )

class PlanAdmin(admin.ModelAdmin):
    list_display = ('order_num', 'name', 'price', 'feature_list')
    ordering = ['order_num', 'name', 'price']
    search_fields = ['order_num', 'name', 'price']

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'agent_list')
    ordering = ['name', 'description']
    search_fields = ['name', 'description']


class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'status')


class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online', 'active_chat')

class FormCustomerAdmin(admin.ModelAdmin):
    list_display = ('name_user',)

class FileFormCustomerAdmin(admin.ModelAdmin):
    list_display = ('name_label', 'file')

class KYCAdmin(admin.ModelAdmin):
    filter_horizontal = ('share_to',)

# Register your models here.
admin.site.register(CategoryCompany)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Feature)
admin.site.register(SiteData)
admin.site.register(HeadCompany)
admin.site.register(AgentRequest)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Agent, AgentAdmin)
admin.site.register(Comment)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(FileFormCustomer, FileFormCustomerAdmin)
admin.site.register(FormCustomer, FormCustomerAdmin)
admin.site.register(Forms)
admin.site.register(KYCInformation, KYCAdmin)
admin.site.register(BrandValue)
admin.site.register(Activity)

class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'product')

admin.site.register(ServiceProvider, ServiceProviderAdmin)

admin.site.register(TimetoResolve)

class WYSIYG(admin.ModelAdmin):
    class Media:
        css = {
             'all': (
                '/media/dashboard/css/font-awesome.css',
                '/media/dashboard/css/bootstrap.min.css',
                '/media/css/custom_admin.css',
                # '/media/dashboard/css/animate.css',
                # '/media/dashboard/css/admin.css',
                '/media/js/WYSIYG/bootstrap-wysihtml5.css',)
            }
        js = (
            '/media/dashboard/js/jquery-2.1.0.js',
            '/media/js/WYSIYG/wysihtml5-0.3.0.js',
            '/media/js/WYSIYG/bootstrap-wysihtml5.js',
            '/media/js/custom_admin.js',
            )
admin.site.register(KYCInstruction, WYSIYG)


class AssignedUserAdmin(admin.ModelAdmin):
    list_display = ('user', )
admin.site.register(AssignedUser, AssignedUserAdmin)
admin.site.register(Notification)
admin.site.register(KYCPartner)
admin.site.register(CompanySettings)