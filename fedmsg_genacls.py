# -*- coding: utf-8 -*-
""" A fedmsg consumer that listens to pkgdb messages to update gitosis acls

Authors:    Janez Nemanič <janez.nemanic@gmail.com>
            Ralph Bean <rbean@redhat.com>

"""

import pprint
import subprocess
import os
import fedmsg.consumers
import moksha.hub.reactor


class GenACLsConsumer(fedmsg.consumers.FedmsgConsumer):

    # Really, we want to use this specific topic to listen to.
    topic = 'org.fedoraproject.prod.pkgdb.acl.update'
    # But for testing, we'll just listen to all topics with this:
    #topic = '*'

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

        moksha.hub.reactor.reactor.callLater(self.delay, delayed_consume)

    def action(self, messages):
        self.log.debug("Acting on %s" % pprint.pformat(messages))

        command = '/usr/bin/sudo -u gen-acls /usr/local/bin/genacls.sh'.split()

        self.log.info("Running %r" % command)
        process = subprocess.Popen(args=command)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            self.log.info("%r was successful" % command)
        else:
            self.log.error("%r exited with %r, stdout: %s, stderr: %s" % (
                command, process.returncode, stdout, stderr))
