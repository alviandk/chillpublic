from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import Context, RequestContext
from django.template.loader import get_template, render_to_string
import json

def dashboard_customer(request):
	# return render_to_response('new_template/customer/dashboard.html', locals(), context_instance=RequestContext(request))
	data    =   render_to_string('new_template/customer/dashboard.html', locals(), context_instance=RequestContext(request))
	resp    =   { 'status': True, 'msg': data }
	return HttpResponse(json.dumps(resp), content_type='application/json')