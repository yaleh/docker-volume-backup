# Docker Volume Backup

Docker Volume Backup is a simple tool to backup and restore Docker volumes for containers and composes.
It requires no access to docker-compose file, and is compatible with Portainer and Docker Compose.

## Installation

### Install with pip

```bash
pip3 install -r requirements.txt
```

## Usage

### Backup

To backup a volume, run the following command:

    docker-volume-backup.py -v <volumes> -d <backup_dir>

To backup volumes of a container, run the following command:

    docker-volume-backup.py -c <containers> -d <backup_dir>

To backup volumes of a compose, run the following command:
    
    docker-volume-backup.py -m <composes> -d <backup_dir>

### Restore

To restore volume(s), run the following command:

    docker-volume-backup.py -r -d <backup_dir>

### Options

    -v, --volumes <volumes>          Volumes to backup, separated by comma
    -c, --containers <containers>    Containers to backup, separated by comma
    -m, --composes <composes>        Composes to backup, separated by comma
    -d, --destination <destination>  Destination to backup to
    --all-volumes                    Backup all volumes
    --all-containers                 Backup all containers
    --all-composes                   Backup all composes
    -r, --restore                    Restore from backup
    -l, --list                       List volumes only, don't backup
    -h, --help                       Display help for command
