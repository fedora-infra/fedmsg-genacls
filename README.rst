fedmsg-genacls
==============

An example of using `fedmsg <http://fedmsg.com>`_ to monitor `pkgdb
<https://admin.fedoraproject.org/pkgdb>`_ for messages, but delaying
action for a few seconds to accumulate messages and avoid pile-up.

Running
-------

.. code-block:: bash

    # Install virtualenvwrapper and restart you terminal
    sudo yum install python-virtualenvwrapper

    # In a new terminal
    mkvirtualenv genacls-fedmsg
    python setup.py develop
    fedmsg-hub

You can tweak the settings in the ``fedmsg.d/`` directory.
