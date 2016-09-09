======================
memcached-registrar
======================

**memcached-registrar** is a command line tool for registering the connection
information for memcached servers in an etcd server.

Requirements
=============

There are a few requirements for running **memcached-registrar**:

 * An etcd server (An etcd cluster is recommended for production environments)
 * Python 3


Installing
=============

Installing from a released tarball is recommended for most people. This
should be done using pip::

    pip install memcached-registrar-${VERSION}.tar.gz


Running
=============

After package installation, a single command line program is available:
``memcached-registrar``. A single running **memcached-registrar** is meant
to be paired with a single memcached server. So, for every memcached server
you want to deploy there should be a registrar to register it in etcd.

For simplicity, I'd recommend that a **memcached-registrar** process runs
in the same deployable unit (VM image or container) as every memcached server.


Development
=============

The development environment can be set up in a virtualenv::

    # Create and activate your virtualenv with your preferred tool
    mkvirtualenv -p python3 registrar

    # Install the package requirements and dev tools
    pip install -r dev-requirements.txt

    # Install the pre-commit hooks for basic code style checking
    pre-commit install
