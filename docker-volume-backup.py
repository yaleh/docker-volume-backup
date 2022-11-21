#!/usr/bin/env python3

import datetime
import json
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

def get_networks(network_names):
    networks = []
    for network_name in network_names:
        networks.append(client.networks.get(network_name))

    return networks

def get_all_networks():
    networks = client.networks.list()
    return networks

def get_networks_by_containers(containers):
    networks = []
    for container in containers:
        network_names = list(container.attrs['NetworkSettings']['Networks'].keys())
        for network_name in network_names:
            network = client.networks.get(network_name)
            # only backup attachable bridge networks
            if network.attrs['Driver'] == 'bridge' and network.attrs['Attachable']:
                networks.append(network)

    return networks

def backup_networks(networks, backup_dir):
    for n in networks:
        # backup attachable bridge networks only
        if n.attrs['Driver'] == 'bridge' and n.attrs['Attachable']:
            print("Backing up network {}".format(n.name))
            os.system("docker network inspect {} > {}".format(n.name, os.path.join(backup_dir, "{}.json".format(n.name))))

def restore_networks(backup_dir):
    for f in os.listdir(backup_dir):
        if f.endswith(".json"):
            network_name = f.replace(".json", "")
            network_json = os.path.join(backup_dir, f)
            network_specs = json.load(open(network_json))

            if network_specs[0]['Attachable'] and network_specs[0]['Driver'] == 'bridge':
                # restore network
                print("Restoring network {}".format(network_name))
                os.system("docker network create --driver bridge --attachable --subnet {} --gateway {} {}".format(network_specs[0]['IPAM']['Config'][0]['Subnet'], network_specs[0]['IPAM']['Config'][0]['Gateway'], network_specs[0]['Name']))

def print_volumes(volumes):
    print("\nVolumes:\n")
    for v in volumes:
        print(v.name)

def print_networks(networks):
    print("\nNetworks:\n")
    for n in networks:
        print(n.name)

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
    files = []
    for v in volumes:
        files.append("{}.tar.gz".format(v.name))

    # generate checksums and remove the path prefix
    os.system("cd {} && sha256sum {} > checksums.sha256".format(backup_dir, " ".join(files)))

def generate_backup_report(volumes, networks, backup_dir):
    volume_report = []
    for v in volumes:
        volume_report.append("{}: {} {}".format(
                                            v.name,
                                            os.path.join(backup_dir, "{}.tar.gz".format(v.name)), 
                                            os.path.getsize(os.path.join(backup_dir, "{}.tar.gz".format(v.name)))
                                        ))

    network_report = []
    for n in networks:
        network_report.append("{}: {} {}".format(
                                            n.name,
                                            os.path.join(backup_dir, "{}.json".format(n.name)), 
                                            os.path.getsize(os.path.join(backup_dir, "{}.json".format(n.name)))
                                        ))

    with open(os.path.join(backup_dir, "backup_report.txt"), "w") as f:
        f.write("Docker Volume Backup\n")
        f.write("{}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        f.write("{}\n".format("=" * 20))
        f.write("\nVolumes:\n\n")
        f.write("\n".join(volume_report))
        f.write("\n")
        f.write("\nNetworks:\n\n")
        f.write("\n".join(network_report))
        f.write("\n")

def verify_backup_checksums(backup_dir):
    checked = os.system("cd {} && sha256sum -c checksums.sha256".format(backup_dir))
    if checked != 0:
        print("Checksums do not match")
        sys.exit(1)

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
    parser.add_argument('--networks', '-n', help='networks to backup')
    parser.add_argument('--all-networks', action='store_true', help='backup all attachable networks')
    parser.add_argument('--backup-dir', '-d', help='backup directory')
    parser.add_argument('--restore', '-r', help='restore volumes', action='store_true')
    parser.add_argument('--no-volume', '-nv', help='do not backup/restore volumes', action='store_true')
    parser.add_argument('--no-network', '-nn', help='do not backup/restore networks', action='store_true')
    parser.add_argument('--list', '-l', action='store_true', help='list volumes and networks only')
    args = parser.parse_args()

    global client
    client = docker.from_env()

    volume_names = args.volumes.split(',') if args.volumes else []
    network_names = args.networks.split(',') if args.networks else []
    container_names = args.containers.split(',') if args.containers else []
    compose_names = get_all_compose_names() if args.all_composes else args.composes.split(',') if args.composes else []
    backup_dir = args.backup_dir if args.backup_dir else os.getcwd()

    find_invalid_containers(container_names)
    containers = get_all_containers() if args.all_containers else (get_containers(container_names) + get_containers_by_composes(compose_names))
    containers = [*set(containers)]
    volumes = get_all_volumes() if args.all_volumes else (get_volumes(volume_names) + get_volumes_from_containers(containers))
    volumes = [*set(volumes)]
    networks = get_all_networks() if args.all_networks else get_networks(network_names)+get_networks_by_containers(containers)
    networks = [*set(networks)]

    if args.list:
        print_volumes(volumes)
        print_networks(networks)
        exit(0)

    if backup_dir is None:
        print("Backup directory not specified")
        exit(1)

    # get absolute path of backup directory
    backup_dir = os.path.abspath(backup_dir)

    if args.no_volume:
        volumes = []
    if args.no_network:
        networks = []

    if args.restore:
        if not args.no_volume:
            verify_backup_checksums(backup_dir)
            restore_volumes(backup_dir)
        if not args.no_network:
            restore_networks(backup_dir)
    else:
        if not args.no_volume:
            backup_volumes(volumes, backup_dir)
            generate_backup_checksums(volumes, backup_dir)
        if not args.no_network:
            backup_networks(networks, backup_dir)
        generate_backup_report(volumes, networks, backup_dir)
        
if __name__ == '__main__':
    main()