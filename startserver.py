#!/usr/bin/python
import subprocess
import sys
import os
import commands
import re

maxspare = 3
minspare = 1
port = 8081

try:
    if sys.argv[1] == 'kill':
        for i in commands.getoutput('ps -ax | grep manage.py').split('\n'):
            if re.search('python manage.py runfcgi maxspare=%s minspare=%s host=127.0.0.1 port=%s --settings=chillpublic.settings' % (maxspare, minspare, port), i):
                if re.search(r'([0-9]+) ', i):
                    os.kill(int(re.search(r'([0-9]+) ', i).groups()[0]), 9)
                    print 'kill: %s' % re.search(r'([0-9]+) ', i).groups()[0]
except Exception:
    smart = subprocess.Popen(['python', 'manage.py', 'runfcgi', 'maxspare=%s' % maxspare, 'minspare=%s' % minspare, 'host=127.0.0.1', 'port=%s' % port, '--settings=chillpublic.settings'])
