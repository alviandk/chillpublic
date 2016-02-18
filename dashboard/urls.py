from django.conf.urls import patterns, include, url

urlpatterns = patterns('dashboard.views',
    url(r'^$', 'dashboard', name='dashboard'),
    url(r'^support/$', 'live_support', name='live-support'),
    # url(r'^service-provider/$', 'live_ticket', name='live-ticket'),
    url(r'^service-provider/$', 'agent_service_provider', name='agent_service_provider'),
    url(r'^agent_change_status/$', 'agent_change_status', name='agent_change_status'),
    
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^tickets/$', 'tickets', name='tickets'),
    url(r'^escalated_tickets/$', 'escalated_tickets', name='escalated_tickets'),
    url(r'^resolved/$', 'resolved', name='resolved'),
    url(r'^forms/company/$', 'forms_company', name='forms_company'),
    url(r'^forms/customer/$', 'forms_customer', name='forms_customer'),

    url(r'^forms/create/$', 'form_create', name='form_create'),
    url(r'^forms/edit/(?P<key>[0-9]+)/$', 'form_edit', name='form_edit'),
    url(r'^forms/delete/$', 'form_delete', name='form_delete'),
    url(r'^get_form_json/$', 'get_form_json', name='get_form_json'),
    url(r'^get_form_ajax/$', 'get_form_ajax', name='get_form_ajax'),
    url(r'^get_form_save/$', 'get_form_save', name='get_form_save'),

    url(r'^company_heads/$', 'company_heads', name='company_heads'),
    url(r'^company_heads/create/$', 'company_heads_create', name='company_heads_create'),
    url(r'^company_heads/edit/(?P<key>[0-9]+)/$', 'company_heads_edit', name='company_heads_edit'),
    url(r'^company_heads/delete/$', 'company_heads_delete', name='company_heads_delete'),

    url(r'^departments/$', 'departments', name='departments'),
    url(r'^departments/create/$', 'department_create', name='department_create'),
    url(r'^departments/edit/(?P<key>[0-9]+)/$', 'department_edit', name='department_edit'),
    url(r'^departments/delete/$', 'department_delete', name='department_delete'),
    url(r'^departments/performance/(?P<key>[0-9]+)/$', 'department_perform', name='department_perform'),
    url(r'^get_department_ajax/$', 'get_department_ajax', name='get_department_ajax'),

    url(r'^agents/$', 'agents', name='agents'),
    url(r'^agents/create/$', 'agent_create', name='agent_create'),
    url(r'^agents/edit/(?P<key>[0-9]+)/$', 'agent_edit', name='agent_edit'),
    url(r'^agents/delete/$', 'agent_delete', name='agent_delete'),
    url(r'^agents/performance/(?P<key>[0-9]+)/$', 'agent_perform', name='agent_perform'),
    url(r'^request_agents/approve/$', 'request_agent_approve', name='request_agent_approve'),
    url(r'^request_agents/delete/$', 'request_agent_delete', name='request_agent_delete'),
    url(r'^request_agents/remove/$', 'request_agent_remove', name='request_agent_remove'),
    url(r'^view/forms/$', 'agent_view_forms', name='agent_view_forms'),

    url(r'^tickets/create/$', 'ticket_create', name='ticket_create'),
    url(r'^tickets/view/$', 'ticket_view', name='ticket_view'),
    url(r'^tickets/view1/$', 'ticket_view1', name='ticket_view1'),
    url(r'^tickets/view2/$', 'ticket_view2', name='ticket_view2'),
    url(r'^tickets/change-status/$', 'ticket_status', name='change-status'),

    url(r'^customer/tickets/create/$', 'customer_ticket_create', name='customer_ticket_create'),
    url(r'^form_customer_edit/$', 'form_customer_edit', name='form_customer_edit'),


    url(r'^remove_session/$', 'remove_session', name='remove_session'),

    url(r'^comment/create/$', 'comment_create', name='comment_create'),
    url(r'^profile/save/$', 'profile_save', name='profile_save'),

    url(r'^kyc/$', 'kyc_verification', name='kyc'),

    url(r'^packages/$', 'packages', name='packages'),
    url(r'^change_packages/$', 'change_packages', name='change_packages'),
    url(r'^notification/$', 'notification', name='notification'),

    url(r'^iframe/$', 'iframe', name='iframe'),
    url(r'^iframe_customer/$', 'iframe_customer', name='iframe_customer'),

    # url(r'^verification_mobile/(?P<val>.*)$', 'verification_mobile', name='verification_mobile'),
    url(r'^api_mobile/$', 'api_mobile', name='api_mobile'),
    url(r'^verify_status/$', 'verify_status', name='verify_status'),

    url(r'^create_pdf/$', 'create_pdf', name='create_pdf'),

    #service provideer
    url(r'^my-service-providers/$', 'service_provider', name='service-provider'),
    url(r'^my-service-providers/detail$', 'lookup_service_provider', name='lookup_service_provider'),
    url(r'^my-service-providers/add-new/$', 'add_new_provider', name='add-new-provider'),
    url(r'^delete_service_provider/$', 'delete_service_provider', name='delete_service_provider'),
    url(r'^add_again_service_provider/$', 'add_again_service_provider', name='add_again_service_provider'),
    url(r'^get_subscribe_provider/$', 'get_subscribe_provider', name='get-subscribe-provider'),
    url(r'^verified-subscribe-provider/$', 'verified_subscribe_provider', name='verified-subscribe-provider'),

    url(r'^kyc-partner/$', 'kyc_partner', name='kyc-partner'),
    url(r'^my-kyc-verification/$', 'my_kyc_verification', name='my-kyc-verification'),

    #kyc & live chat settings
    url(r'^settings/$', 'company_settings', name='settings'),

)

#ajax
urlpatterns += patterns('dashboard.ajax',
    url(r'^ajax-post-share/', 'ajax_post_share', name="ajax-post-share"),
)   


