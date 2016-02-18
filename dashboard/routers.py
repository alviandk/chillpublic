from swampdragon import route_handler
from swampdragon.route_handler import BaseRouter


class ChatRouter(BaseRouter):
    route_name = 'chat-route'
    valid_verbs = ['chat', 'subscribe']

    def get_subscription_channels(self, **kwargs):
        return ['chatroom']

    def chat(self, *args, **kwargs):
        errors = {}

        if 'message' not in kwargs or len(kwargs['message']) is 0:
            errors['message'] = 'Enter a chat messge'

        if errors:
            self.send_error(errors)
        else:
            self.send({'status': 'ok'})
            self.publish(self.get_subscription_channels(), kwargs)

        # print(request)


route_handler.register(ChatRouter)