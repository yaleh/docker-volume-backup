# Docker Volume Backup

Docker Volume Backup is a simple tool to backup and restore Docker volumes for containers and composes.
It requires no access to docker-compose file, and is compatible with Portainer and Docker Compose.

## Usage

### Backup

To backup a volume, run the following command:

    docker-volume-backup -v <volume> -d <destination>

To backup volumes of a container, run the following command:

    docker-volume-backup -c <container> -d <destination>

To backup volumes of a compose, run the following command:
    
    docker-volume-backup -m <compose> -d <destination>

### Restore

To restore volume(s), run the following command:

    docker-volume-backup -r -d <destination>

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