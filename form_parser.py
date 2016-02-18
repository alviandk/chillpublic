import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chillpublic.settings")

from accounts.models import *
from pyquery import PyQuery as pq
import json

def parse():
    data = Forms.objects.get().form_content
    d = pq(data)
    result = []
    for i in d('.component'):
        c = pq(i.attrib['data-content'])
        json_input = open('media/js/form_builder/data/input.json').read()
        input_data = json.loads(json_input)
        for x in input_data:
            if x['title'] == i.attrib['data-title']:
                result.append(x)

    return json.dumps(result)

print parse()