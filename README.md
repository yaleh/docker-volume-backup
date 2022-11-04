# Docker Volume Backup

Docker Volume Backup is a simple tool to backup and restore Docker volumes and attachable networks
for containers and composes. It requires no access to docker-compose file, and is compatible with
Portainer and Docker Compose.

## Installation

### Install with pip

```bash
pip3 install -r requirements.txt
```

## Usage

### Backup

To backup a volume, run the following command:

    docker-volume-backup.py -v <volume> -d <backup_dir>

To backup multiple volumes, use a comma-separated list:

    docker-volume-backup.py -v <volume1>,<volume2>,<volume3> -d <backup_dir>

To backup a network, run the following command:

    docker-volume-backup.py -n <network> -d <backup_dir>

To backup multiple networks, use a comma-separated list:

    docker-volume-backup.py -n <network1>,<network2>,<network3> -d <backup_dir>

To backup volumes and attachable networks of a container, run the following command:

    docker-volume-backup.py -c <container> -d <backup_dir>

To backup volumes and attachable networks of multiple containers, use a comma-separated list:

    docker-volume-backup.py -c <container1>,<container2>,<container3> -d <backup_dir>

To backup volumes and attachable networks of a compose, run the following command:
    
    docker-volume-backup.py -m <compose> -d <backup_dir>

To backup volumes and attachable networks of multiple composes, use a comma-separated list:

    docker-volume-backup.py -m <compose1>,<compose2>,<compose3> -d <backup_dir>
    
### Restore

To restore volume(s), run the following command:

    docker-volume-backup.py -r -d <backup_dir>

### Options

    -v, --volumes <volumes>          Volumes to backup, separated by comma
    -n, --networks <networks>        Networks to backup, separated by comma
    -c, --containers <containers>    Containers to backup, separated by comma
    -m, --composes <composes>        Composes to backup, separated by comma
    -d, --destination <destination>  Destination to backup to
    --all-volumes                    Backup all volumes
    --all-containers                 Backup volumes of all containers
    --all-composes                   Backup volumes of all composes
    -nv, --no-volumes                Do not backup volumes
    -nn, --no-networks               Do not backup networks
    -r, --restore                    Restore from backup
    -l, --list                       List volumes only, don't backup
    -h, --help                       Display help for command
