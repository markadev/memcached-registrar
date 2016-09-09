#!/usr/bin/env python3

import argparse
import docker
import etcd
import json
import logging
import os
from pymemcache.client.base import Client
import time
from urllib.parse import urlparse


logger = logging.getLogger('memcached-registrar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Register memcached in a service registry')
    parser.add_argument('--registry',
        default=os.environ.get('REGISTRY', None),
        help='URL of the etcd server (etcd://host:port/path/to/service')
    parser.add_argument('--internal-addr',
        default=os.environ.get('MEMCACHED_INTERNAL_ADDR', '127.0.0.1'),
        help='Internal address of memcached [127.0.0.1]')
    parser.add_argument('--internal-port', type=int,
        default=os.environ.get('MEMCACHED_INTERNAL_PORT', 11211),
        help='Internal port of memcached [11211]')
    parser.add_argument('--public-addr',
        default=os.environ.get('MEMCACHED_PUBLIC_ADDR', None),
        help='External address of memcached, registered with the registry')
    parser.add_argument('--public-port', type=int,
        help='External port of memcached, registered with the registry')
    parser.add_argument('--ttl', type=int, default=60,
        help='TTL for etcd entries')
    parser.add_argument('--weight',
        help='Memcached instance weight. Defaults to the # of MBs of ' +
             'memory memcached is allocated')

    return parser.parse_args()


def get_docker_env_values(args):
    """Try to fill in missing arguments from the Docker environment"""

    try:
        # In a container, the hostname is the container ID
        container_id = os.environ['HOSTNAME']
        cli = docker.Client(base_url='unix://var/run/docker.sock')
        container_info = cli.inspect_container(container_id)
    except KeyError:
        logger.warn("HOSTNAME environment variable is not set")
        return
    except:
        logger.warn("Unable to inspect this container")
        return

    # Inspect our container settings to determine memcached's external IP
    # and port.
    if args.public_addr is None:
        port_mappings = container_info['NetworkSettings']['Ports']
        memcached_mappings = port_mappings['{}/tcp'.format(args.internal_port)]
        ip = memcached_mappings[0]['HostIp']
        if ip != '0.0.0.0':
            args.public_addr = ip
        else:
            logger.warn("Unable to determine public IP address from " +
                "container configuration. Specify it manually.")
    if args.public_port is None:
        port_mappings = container_info['NetworkSettings']['Ports']
        memcached_mappings = port_mappings['{}/tcp'.format(args.internal_port)]
        port = int(memcached_mappings[0]['HostPort'])
        args.public_port = port


def verify_required_args(args):
    if args.registry is None:
        logger.error("No etcd server was specified")
        raise SystemExit(1)
    if args.public_addr is None:
        logger.error("The memcached server public address was not specified")
        raise SystemExit(1)
    if args.public_port is None:
        logger.error("The memcached server public port was not specified")
        raise SystemExit(1)


def registrar_loop(args):
    # Loop until we can inspect the memcached server's size
    while args.weight is None:
        mc = Client((args.internal_addr, args.internal_port))
        try:
            args.weight = int(mc.stats()[b'limit_maxbytes'] / (1024 * 1024))
            if args.weight == 0:
                args.weight = 1
        except:
            logger.warn("Unable to connect to memcached. Will retry.")
            time.sleep(15)
    logger.info('memcached server weight is %s', args.weight)

    metadata_json = json.dumps({
        'host': args.public_addr,
        'port': args.public_port,
        'weight': args.weight,
    })

    registry_url = urlparse(args.registry)

    etcd_key = "{}/{}:{}".format(registry_url.path.rstrip('/'),
        args.public_addr, args.public_port)
    etclient = None

    exiting = False
    while not exiting:
        try:
            if etclient is None:
                etclient = etcd.Client(
                    host=registry_url.netloc,
                    port=registry_url.port
                        if registry_url.port is not None else 2379,
                    allow_reconnect=True,
                    protocol='http')
                etclient._comparison_conditions.add('refresh')

            # Write the key
            logger.info("Registering service")
            etclient.write(etcd_key, metadata_json, args.ttl)

            # Periodically refresh the key
            while True:
                time.sleep(args.ttl * 3 / 4)

                logger.debug("Refreshing service entry")
                etclient.write(etcd_key, None, ttl=args.ttl,
                    prevExist=True, refresh='true')
        except KeyboardInterrupt:
            exiting = True
            break
        except etcd.EtcdKeyNotFound:
            logger.warn('We were unable to refresh our service before it ' +
                'expired. Reregistering. Do consider raising the TTL.')
            # Continue with the outer loop
        except etcd.EtcdException:
            logger.warn('Communication to etcd lost. Will retry.')
            time.sleep(60)
            # Continue with the outer loop

    logger.info("Unregistering service")
    try:
        etclient.delete(etcd_key)
    except:
        pass


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_args()
    get_docker_env_values(args)
    verify_required_args(args)
    registrar_loop(args)


if __name__ == '__main__':
    main()

# vim:set ts=4 sw=4 expandtab:
