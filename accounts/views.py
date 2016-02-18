from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from accounts.models import Customer

import json

# Create your views here.
def registration_success(request, template_name='registration_success.html'):
	return TemplateResponse(request, template_name)

