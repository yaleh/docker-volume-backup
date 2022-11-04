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

def generate_backup_checksums(volumes, backup_dir):
    for v in volumes:
        v_backup = os.path.join(backup_dir, "{}.tar.gz".format(v.name))
        if os.path.isfile(v_backup):
            os.system("sha256sum {} > {}.sha256".format(v_backup, v_backup))

def verify_backup_checksums(backup_dir):
    for f in os.listdir(backup_dir):
        if f.endswith(".tar.gz"):
            volume_name = f.replace(".tar.gz", "")
            print("Verifying volume {}".format(volume_name))
            if not os.path.isfile("{}.sha256".format(f)):
                print("Checksum file not found for volume {}".format(volume_name))
                sys.exit(1)
            os.system("sha256sum -c {}.sha256".format(os.path.join(backup_dir, volume_name))) or sys.exit(1)

def get_all_volumes():
    volumes = client.volumes.list()
    return volumes

def get_all_containers():
    containers = client.containers.list()
    return containers

def get_all_compose_names():
    compose_names = []
    for c in get_all_containers():
        if 'com.docker.compose.project' in c.attrs['Config']['Labels']:
            compose_names.append(c.attrs['Config']['Labels']['com.docker.compose.project'])

    return [*set(compose_names)]

def main():
    parser = argparse.ArgumentParser(description='Backup docker volumes')
    parser.add_argument('--volumes', '-v', help='volumes to backup')
    parser.add_argument('--all-volumes', action='store_true', help='backup all volumes')
    parser.add_argument('--containers', '-c', help='containers to backup')
    parser.add_argument('--all-containers', action='store_true', help='backup all containers')
    parser.add_argument('--composes', '-m', help='composes to backup')
    parser.add_argument('--all-composes', action='store_true', help='backup all composes')
    parser.add_argument('--backup-dir', '-d', help='backup directory')
    parser.add_argument('--restore', '-r', help='restore volumes', action='store_true')
    parser.add_argument('--list', '-l', action='store_true', help='list volumes only')
    args = parser.parse_args()

    global client
    client = docker.from_env()

    volume_names = args.volumes.split(',') if args.volumes else []
    container_names = args.containers.split(',') if args.containers else []
    compose_names = get_all_compose_names() if args.all_composes else args.composes.split(',') if args.composes else []
    backup_dir = args.backup_dir if args.backup_dir else os.getcwd()

    find_invalid_containers(container_names)
    containers = get_all_containers() if args.all_containers else (get_containers(container_names) + get_containers_by_composes(compose_names))
    containers = [*set(containers)]
    volumes = get_all_volumes() if args.all_volumes else (get_volumes(volume_names) + get_volumes_from_containers(containers))
    volumes = [*set(volumes)]

    if args.list:
        print_volumes(volumes)
        exit(0)

    if backup_dir is None:
        print("Backup directory not specified")
        exit(1)

    if args.restore:
        restore_volumes(backup_dir)
        verify_backup_checksums(backup_dir)
    else:
        backup_volumes(volumes, backup_dir)
        generate_backup_checksums(volumes, backup_dir)
        
if __name__ == '__main__':
    main()