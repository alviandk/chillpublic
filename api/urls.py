from django.conf.urls import patterns, include, url

urlpatterns = patterns('api.views',
    url(r'^ticket_resp/$', 'ticket_resp', name='ticket_resp'),
    url(r'^pull-ticket/$', 'pull_ticket', name='pull-ticket'),
    url(r'^load_chat/$', 'load_chat', name='load_chat'),
    url(r'^realtime_get_notification/$', 'realtime_get_notification', name='realtime_get_notification'),
    url(r'^update_notification/$', 'update_notification', name='update_notification'),
    url(r'^count_open/$', 'count_open', name='count_open'),
    url(r'^count_hold/$', 'count_hold', name='count_hold'),
    url(r'^count_resolved/$', 'count_resolved', name='count_resolved'),
    url(r'^count_closed/$', 'count_closed', name='count_closed'),
    url(r'^count_reopen/$', 'count_reopen', name='count_reopen'),
    url(r'^count_assigned/$', 'count_assigned', name='count_assigned'),
    url(r'^check_company_setting/$', 'check_company_setting', name='check_company_setting'),
)
