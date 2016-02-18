from django.conf.urls import patterns, include, url

urlpatterns = patterns('captcha.views',
    url(r'image/(?P<key>\w+)/$', 'captcha_image', name='captcha-image'),
    url(r'audio/(?P<key>\w+)/$', 'captcha_audio', name='captcha-audio'),
)
