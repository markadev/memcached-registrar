from setuptools import find_packages, setup


setup(
    name = 'memcached-registrar',
    description = 'Sidekick for memcached to register containerized instances in a service directory',
    packages = find_packages(),
    install_requires = [
        'python-etcd',
        'pymemcache',
        'docker-py',
    ],

    entry_points = {
        'console_scripts': ['memcached-registrar=registrar.memcached:main'],
    },

    use_scm_version = True,
    setup_requires = ['setuptools_scm'],
)

# vim:set ts=4 sw=4 expandtab:
