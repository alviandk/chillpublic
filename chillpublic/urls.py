from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.index', name='index'),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^login/$', 'app.views.login', name='login'),
    url(r'^activate/(?P<key>[a-fA-F0-9]+)/$', 'app.views.activate', name='activate'),
    url(r'^activation_success/$', 'app.views.activation_success', name='activation_success'),
    url(r'^signup/customer/$', 'app.views.signup_customer', name='signup_customer'),
    url(r'^signup/company/$', 'app.views.signup_company', name='signup_company'),
    url(r'^pricing/$', 'app.views.pricing', name='pricing'),

    url(r'^resend-activation-email/$', 'app.views.resend_activation_email', name='resend-activation-email'),
    url(r'^resend-activation-phone/$', 'app.views.resend_activation_phone', name='resend-activation-phone'),

    # url(r'^logout/$', 'django.contrib.auth.views.logout',{'next_page': '/'}, name='logout'),
    url(r'^logout/$', 'app.views.logout', name='logout'),
    url(r'^register-success/$', 'app.views.registration_success', name='registration_success'),
    url(r'^get_captcha/$', 'app.views.get_captcha', name='get_captcha'),

    url(r'^social/', include('social_auth.urls')),

    url("", include('django_socketio.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^captcha/', include('captcha.urls')),

    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT,}),
)
