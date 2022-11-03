#!/usr/bin/env python

import os
import sys
import docker
import argparse

client = None

def get_containers(container_names):
    containers = []
    for container_name in container_names:
        containers.append(client.containers.get(container_name))

    return containers

def get_containers_by_composes(compose_names):
    containers = []
    for compose_name in compose_names:
        compose_containers = client.containers.list(filters={'label': 'com.docker.compose.project={}'.format(compose_name)})
        containers.extend(compose_containers)

    return containers

def find_invalid_containers(container_names):
    for container_name in container_names:
        try:
            client.containers.get(container_name)
        except docker.errors.NotFound:
            print("Container {} not found".format(container_name))
            sys.exit(1)

    return False

def get_volumes_from_containers(containers):
    volumes = []
    for container in containers:
        mounts = container.attrs['Mounts']
        for m in mounts:
            if m['Type'] == 'volume':
                volumes.append(client.volumes.get(m['Name']))

    return volumes

def get_volumes(volume_names):
    volumes = []
    for volume_name in volume_names:
        volumes.append(client.volumes.get(volume_name))

    return volumes

def print_volumes(volumes):
    for v in volumes:
        print(v.name)

def backup_volumes(volumes, backup_dir):
    for v in volumes:
        print("Backing up volume {}".format(v.name))
        os.system("docker run --rm -v {}:/volume -v {}:/backup ubuntu tar cvfz /backup/{}.tar.gz /volume".format(v.name, backup_dir, v.name))

def restore_volumes(backup_dir):
    for f in os.listdir(backup_dir):
        if f.endswith(".tar.gz"):
            volume_name = f.replace(".tar.gz", "")
            print("Restoring volume {}".format(volume_name))
            os.system("docker run --rm -v {}:/volume -v {}:/backup ubuntu tar xvfz /backup/{}.tar.gz".format(volume_name, backup_dir, volume_name))

def main():
    parser = argparse.ArgumentParser(description='Backup docker volumes')
    parser.add_argument('--volumes', '-v', help='volumes to backup')
    parser.add_argument('--containers', '-c', help='containers to backup')
    parser.add_argument('--composes', '-m', help='composes to backup')
    parser.add_argument('--backup-dir', '-d', help='backup directory')
    parser.add_argument('--restore', '-r', help='restore volumes', action='store_true')
    parser.add_argument('--list', '-l', action='store_true', help='list volumes only')
    args = parser.parse_args()

    volume_names = args.volumes.split(',') if args.volumes else []
    container_names = args.containers.split(',') if args.containers else []
    compose_names = args.composes.split(',') if args.composes else []

    global client
    client = docker.from_env()

    find_invalid_containers(container_names)
    containers = get_containers(container_names)+(get_containers_by_composes(compose_names))
    volumes = get_volumes(volume_names)+(get_volumes_from_containers(containers))
    volumes = [*set(volumes)]

    if args.list:
        print_volumes(volumes)
        exit(0)

    if args.restore:
        restore_volumes(args.backup_dir)
    else:
        backup_volumes(volumes, args.backup_dir)
        
if __name__ == '__main__':
    main()