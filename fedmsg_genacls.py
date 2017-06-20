# -*- coding: utf-8 -*-
""" A fedmsg consumer that listens to pkgdb messages to update gitosis acls

Authors:    Janez Nemanič <janez.nemanic@gmail.com>
            Ralph Bean <rbean@redhat.com>

"""

import pprint
import subprocess
import os

import arrow
import fedora.client.fas2
import fedmsg.consumers
import moksha.hub.reactor


gitolite_template = """
@admins = {admins}
@provenpackager = {provenpackager}
@fedora-arm = {fedora_arm}
@fedora-s390 = {fedora_s390}
@fedora-ppc = {fedora_ppc}

repo @all
    -   VREF/update-block-push-origin = @all
    RWC = @admins @fedora-arm @fedora-s390 @fedora-ppc
    R = @all
"""


class GitolitePrefixConsumer(fedmsg.consumers.FedmsgConsumer):
    """ This is the new-world consumer that handles things for
    pagure-over-dist-git.
    """
    topic = [
        'org.fedoraproject.prod.fas.group.member.sponsor',
        'org.fedoraproject.prod.fas.group.member.remove',

        'org.fedoraproject.stg.fas.group.member.sponsor',
        'org.fedoraproject.stg.fas.group.member.remove',

        'org.fedoraproject.dev.fas.group.member.sponsor',
        'org.fedoraproject.dev.fas.group.member.remove',
    ]
    interesting_groups = dict(
        admins='releng-team',
        provenpackager='provenpackager',
        fedora_arm='fedora-arm',
        fedora_s390='fedora-s390',
        fedora_ppc='fedora-ppc',
    )
    config_key = 'gitoliteprefix.consumer.enabled'

    def __init__(self, hub):
        super(GitolitePrefixConsumer, self).__init__(hub)

        # This is required.  It is the number of seconds that we should wait
        # until we ultimately act on a FAS message.
        self.delay = self.hub.config['gitoliteprefix.consumer.delay']
        # Also required.  This is the location we write our file to.
        self.filename = self.hub.config['gitoliteprefix.consumer.filename']

        # Some required FAS connection details
        self.fasurl = self.hub.config['gitoliteprefix.consumer.fasurl']
        self.username = self.hub.config['gitoliteprefix.consumer.username']
        self.password = self.hub.config['gitoliteprefix.consumer.password']

        # We use this to manage our state
        self.queued_messages = []

        # If our file doesn't exist on startup, then write it.
        if not os.path.exists(self.filename):
            self.action(None)
        else:
            self.log.info("Found %r, not overwriting." % self.filename)
            ago = arrow.get(os.stat(self.filename).st_mtime).humanize()
            self.log.warn("%s last modified %s" % (self.filename, ago))

    def consume(self, msg):
        msg = msg['body']

        if msg['msg']['group'] not in self.interesting_groups.values():
            return

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

        self.log.info("Gathering gitolite admin groups from FAS.")
        groups = self.gather_admin_groups()

        self.log.info("Writing to %r" % self.filename)
        with open(self.filename, 'w') as f:
            f.write(gitolite_template.format(**groups))
        self.log.debug("Done.")

    def gather_admin_groups(self):
        fas = fedora.client.AccountSystem(
            self.fasurl, username=self.username, password=self.password)
        result = dict()
        for gitolite_group, fas_group in self.interesting_groups.items():
            self.log.info("Querying FAS for group %r" % fas_group)
            result[gitolite_group] = " ".join(list(sorted([
                user['username'] for user in fas.people_by_groupname(fas_group)
            ])))
        return result


class GenACLsConsumer(fedmsg.consumers.FedmsgConsumer):
    """ This is the old-world consumer that handles gitolite perms for back
    before we had pagure over dist-git.
    """

    # Because we are interested in a variety of topics, we tell moksha that
    # we're interested in all of them (it doesn't know how to do complicated
    # distinctions).  But then we'll filter later in our consume() method.
    topic = '*'
    interesting_topics = [
        'org.fedoraproject.prod.pkgdb.acl.update',
        'org.fedoraproject.prod.pkgdb.acl.delete',
        'org.fedoraproject.prod.fas.group.member.sponsor',
        'org.fedoraproject.prod.fas.group.member.remove',
        'org.fedoraproject.prod.pkgdb.package.new',
        'org.fedoraproject.prod.pkgdb.package.delete',
        'org.fedoraproject.prod.pkgdb.package.branch.new',
        'org.fedoraproject.prod.pkgdb.package.branch.delete',
        'org.fedoraproject.prod.pkgdb.owner.update',

        'org.fedoraproject.stg.pkgdb.acl.update',
        'org.fedoraproject.stg.pkgdb.acl.delete',
        'org.fedoraproject.stg.fas.group.member.sponsor',
        'org.fedoraproject.stg.fas.group.member.remove',
        'org.fedoraproject.stg.pkgdb.package.new',
        'org.fedoraproject.stg.pkgdb.package.delete',
        'org.fedoraproject.stg.pkgdb.package.branch.new',
        'org.fedoraproject.stg.pkgdb.package.branch.delete',
        'org.fedoraproject.stg.pkgdb.owner.update',
    ]

    config_key = 'genacls.consumer.enabled'

    def __init__(self, hub):
        super(GenACLsConsumer, self).__init__(hub)

        # This is required.  It is the number of seconds that we should wait
        # until we ultimately act on a pkgdb message.
        self.delay = self.hub.config['genacls.consumer.delay']

        # We use this to manage our state
        self.queued_messages = []

    def consume(self, msg):
        if msg['topic'] not in self.interesting_topics:
            return

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

        command = '/usr/bin/sudo -u root /usr/local/bin/genacls.sh'.split()

        self.log.info("Running %r" % command)
        process = subprocess.Popen(args=command)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            self.log.info("%r was successful" % command)
        else:
            self.log.error("%r exited with %r, stdout: %s, stderr: %s" % (
                command, process.returncode, stdout, stderr))
