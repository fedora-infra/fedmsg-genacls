# An fedmsg consumer that listens to pkgdb messages and update gitosis acls

import fedmsg.consumers

import pprint

from moksha.hub.reactor import reactor


class GenACLsConsumer(fedmsg.consumers.FedmsgConsumer):

    # Really, we want to use this specific topic to listen to.
    #topic = 'org.fedoraproject.prod.pkgdb.acl.update'
    # But for testing, we'll just listen to all topics with this:
    topic = '*'

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
        # TODO -- implement the real work stuff to do here...
