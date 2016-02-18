from accounts.models import *
from datetime import *

def ticket_time():
	#get datetime now
	now = datetime.now()

	#get list ticket status is not resolve
	ls_ticket = Ticket.objects.exclude(status = '3')

	#loop ticket where status is not resolve
	for data in ls_ticket:
		get_created = data.timestamp

		#now - created
		get_total_time = now - get_created.replace(tzinfo=None)
		secs = get_total_time.total_seconds()

		hours = int(secs / 3600)

		#update time to resolve
		up_time = TimetoResolve.objects.get(ticket = data)
		# up_time.time = hours
		#remaining time
		remaining = up_time.time - hours
		if remaining <= 0:
			up_time.time = 0
		else:
			up_time.time = remaining
		up_time.save()

