from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib import auth
from django.conf import settings
from django.contrib.auth.decorators import login_required
from accounts.models import *
import json


#post ajax share kyc
@login_required
def ajax_post_share(request):
	if request.method == 'POST' and request.is_ajax():
		kyc = KYCInformation.objects.get(id = request.POST.get('kyc_id'))
		for data in request.POST.getlist('department[]'):
			get_department = Department.objects.get(id = data)
			kyc.share_to.add(get_department)
		kyc.save()
		resp = {'status': True, 'msg': 'success'}
	else:
		resp = {'status': False, 'msg': 'failed'}
	return HttpResponse(json.dumps(resp), content_type='application/json')