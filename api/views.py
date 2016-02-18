from django.http import HttpResponse
from accounts.models import *
from django.core.serializers.json import DjangoJSONEncoder
from django_socketio import broadcast, broadcast_channel, NoSocket
from django.contrib.auth.decorators import login_required
from datetime import datetime
import json


def ticket_resp(request):
    user = str(request.user)
    ticket_id = request.GET.get('id')

    if request.is_agent:
    	# assigned = AssignedUser.objects.create(user = request.user, timestamp = datetime.now())
    	get_ticket = Ticket.objects.get(id = ticket_id)
    	# get_ticket.assigned = assigned
        # get_ticket.status = '6'
    	# get_ticket.save()


    message = 'has ben joined chat'
    data = {"user": user, "message": message}
    broadcast_channel(data, channel="room-" + ticket_id)
    return HttpResponse('ok')


@login_required
def pull_ticket(request):
    try:
        ticket_id = request.GET.get('id')
        assigned = AssignedUser.objects.create(user = request.user, timestamp = datetime.now())
        get_ticket = Ticket.objects.get(id = ticket_id)
        get_ticket.assigned = assigned
        get_ticket.status = '6'
        get_ticket.save()
        return HttpResponse('1')
    except:
        pass



def chat_api(data, channel):
    broadcast_channel(data, channel)


@login_required
def load_chat(request):
    key = request.GET.get('id')
    # request.session['chat_id'] = key
    try:
        # lookup            = (Ticket.objects.select_related('author').get(id = key))
        lookup = Ticket.objects.get(id = key)
        lookup.online = True
        t = lookup.save()
        if lookup.status != '4':
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

        resp = {'status': True, 'msg': 'success', 'key':lookup.id, 'message_info': '', }
        # broadcast_channel(lookup.id, channel="channel-"+str(lookup.assigned.user.id))
        data = {"agent": str(lookup.assigned.user), "id": lookup.id}
        broadcast_channel(data, channel="channel-"+str(lookup.assigned.user.id)) #broadcast / send message into agent channel
    except Exception, err:
        resp = {'status': False, 'msg': unicode(err), 'key':''}

    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def realtime_get_notification(request):
    z = Notification.objects.filter(to = request.user, read = False).order_by('-id')
    message = []
    for obj in z:
    #     message.append(obj.data)
        if obj.notif_type == 1:
            try:
                result = Ticket.objects.get(id=obj.ref_id)
                str_data = 'Ticket %s state changed into %s' % (result.id, result.get_status_display())
                message.append({'message':str_data, 'id':obj.ref_id, 'notif_id': obj.id})
            except:
                pass
        else:
            result = Comment.objects.get(id=obj.ref_id)
            get_ticket = result.ticket_set.all()[:1]
            get_ticket_id = ''
            for data in get_ticket:
                get_ticket_id = data.id
            # str_data = '%s add comment' % result.user
            str_data = 'New Comment in ticket %s' % get_ticket_id
            message.append({'message':str_data, 'id':get_ticket_id, 'notif_id': obj.id})
    resp = {'count': len(z), 'message': message }
    return HttpResponse(json.dumps(resp), content_type='application/json')



@login_required
def update_notification(request):
    try:
        get_notif = Notification.objects.get(id = request.GET.get('id'))
        get_notif.read = True
        get_notif.save()
        return HttpResponse('success')
    except Exception, e:
        return HttpResponse(e)


@login_required
def count_open(request):
    q = Ticket.objects.filter(author = request.user, status = '1').count()
    return HttpResponse(q)

@login_required
def count_hold(request):
    q = Ticket.objects.filter(author = request.user, status = '2').count()
    return HttpResponse(q)

@login_required
def count_resolved(request):
    q = Ticket.objects.filter(author = request.user, status = '3').count()
    return HttpResponse(q)

@login_required
def count_closed(request):
    q = Ticket.objects.filter(author = request.user, status = '4').count()
    return HttpResponse(q)

@login_required
def count_reopen(request):
    q = Ticket.objects.filter(author = request.user, status = '5').count()
    return HttpResponse(q)

@login_required
def count_assigned(request):
    q = Ticket.objects.filter(author = request.user, status = '6').count()
    return HttpResponse(q)

@login_required
def check_company_setting(request):
    # if request.GET.get('company'):
    try:
        resp = {}
        get_company_setting = CompanySettings.objects.get(company__id = request.GET.get('company'))
        if get_company_setting.kyc_mandatory == True:
            #check user kyc
            try:
                check_kyc = KYCInformation.objects.get(user__username = request.GET.get('user'))
                resp['kyc_user_validate'] = True
            except Exception, e:
                resp['kyc_user_validate'] = False

        else:
            resp['kyc_user_validate'] = True


        if get_company_setting.live_chat == True:
            resp['allow_chat'] = True
        else:
            try:
                ServiceProvider.objects.get(user__username = request.GET.get('user'), company__id = request.GET.get('company'), product__id = request.GET.get('department'))
                resp['allow_chat'] = True
            except Exception, e:
                print(e);
                resp['allow_chat'] = False


        return HttpResponse(json.dumps(resp), content_type='application/json')

    except Exception, e:
        return HttpResponse(e)
