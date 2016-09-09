from setuptools import find_packages, setup


setup(
    name = 'memcached-registrar',
    description = 'Register memcached servers in etcd',
    long_description = open('README.rst').read(),
    author = 'Mark Aikens',
    author_email = 'markadev@primeletters.net',
    license = 'MIT',
    url = 'https://github.com/markadev/memcached-registrar',

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
