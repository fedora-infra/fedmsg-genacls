# An fedmsg consumer that listens to pkgdb messages and update gitosis acls

import fedmsg.consumers

import pprint

from moksha.hub.reactor import reactor

import json
import httplib
import subprocess


class GenACLsConsumer(fedmsg.consumers.FedmsgConsumer):

    # Really, we want to use this specific topic to listen to.
    #topic = 'org.fedoraproject.prod.pkgdb.acl.update'
    # But for testing, we'll just listen to all topics with this:
    #topic = '*'

    topic = 'org.fedoraproject.prod.pkgdb.acl.update'

    config_key = 'genacls.consumer.enabled'

    def __init__(self, hub):
        super(GenACLsConsumer, self).__init__(hub)

        # This is required.  It is the number of seconds that we should wait
        # until we ultimately act on a pkgdb message.
        self.delay = self.hub.config['genacls.consumer.delay']

        # We use this to manage our state
        self.queued_messages = []

    def consume(self, msg):
        msg = msg['body']
        self.log.info("Got a message %r" % msg['topic'])

        def delayed_consume():
            if self.queued_messages:
                try:
                    self.action(self.queued_messages)
                finally:
                    # Empty our list at the end of the day.
                    self.queued_messages = []
            else:
                self.log.debug("Woke up, but there were no messages.")

        self.queued_messages.append(msg)

        reactor.callLater(self.delay, delayed_consume)

    def action(self, messages):
        self.log.info("Acting on %r" % pprint.pformat(messages))
        username = None
        for message in messages:
            msg = message['msg']

            if msg['status'] == 'Awaiting Review':
                continue

            # if username in message is different from the one in previous
            # message query the pkgdb for username's acls, else use the old
            # acls
            if msg['username'] != username:
                username = msg['username']
                connection = httplib.HTTPConnection("209.132.184.188")
                getquery = '/api/packager/acl/{0}'.format(username)
                connection.request("GET", getquery)
                response = connection.getresponse().read()
                useracls = json.loads(response)

            # check if collection{branchname,name,version}, package{name}, acl,
            # status, username... match in pkgdb and fedmsg message, if there
            # is a match run genacls script
            for packageacl in useracls['acls']:
                if (
                    msg['package_listing']['package']['name'] == packageacl['packagelist']['package']['name'] and
                    msg['acl'] == packageacl['acl'] and
                    msg['package_listing']['collection']['branchname'] == packageacl['packagelist']['collection']['branchname'] and
                    msg['package_listing']['collection']['name'] == packageacl['packagelist']['collection']['name'] and
                    msg['package_listing']['collection']['version'] == packageacl['packagelist']['collection']['version'] and
                    msg['username'] == packageacl['fas_name']
                ):

                    subprocess.call('/usr/local/bin/genacls.sh')
                    self.queued_messages = []
                    return
                    #genacls will update all acls so
                    #clean messages queue and return
