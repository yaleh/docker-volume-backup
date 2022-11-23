#!/usr/bin/env python3

import datetime
import json
import os
import sys
import docker
import argparse
import requests

class PortainerClient:
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.token = None

    def login(self):
        url = self.endpoint + '/api/auth'
        data = {'Username': self.username, 'Password': self.password}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 200:
            self.token = r.json()['jwt']
            return True
        else:
            print("Portainer login failed with status code " + str(r.status_code))
            return False

    def logout(self):
        url = self.endpoint + '/api/auth/logout'
        headers = {'Authorization': 'Bearer ' + self.token}
        r = requests.post(url, headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            return True
        else:
            print("Portainer logout failed with status code " + str(r.status_code))
            return False

    def get_stacks(self):
        url = self.endpoint + '/api/stacks'
        headers = {'Authorization': 'Bearer ' + self.token}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            print("Portainer get stacks failed with status code " + str(r.status_code))
            return False

    def get_stack_file(self, stack_id):
        url = self.endpoint + '/api/stacks/' + str(stack_id) + '/file'
        headers = {'Authorization': 'Bearer ' + self.token}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.text
        else:
            print("Portainer get stack file failed with status code " + str(r.status_code))
            return False

    def create_stack(self, stack_name, stack_file):
        url = self.endpoint + '/api/stacks'
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}
        data = {'Name': stack_name, 'SwarmID': 'local', 'StackFileContent': stack_file}
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if r.status_code == 201:
            return True
        else:
            print("Portainer create stack failed with status code " + str(r.status_code))
            return False

    def delete_stack(self, stack_id):
        url = self.endpoint + '/api/stacks/' + str(stack_id)
        headers = {'Authorization': 'Bearer ' + self.token}
        r = requests.delete(url, headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            return True
        else:
            print("Portainer delete stack failed with status code " + str(r.status_code))
            return False

# Portainer user login
#   returns token in JSON, None on failure
def portainer_login(endpoint, username, password):
    url = endpoint + '/api/auth'
    data = {'Username': username, 'Password': password}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 200:
        return r.json()
    else:
        print("Portainer login failed with status code " + str(r.status_code))
        return None

# Portainer user logout
#   returns True if successful
def portainer_logout(endpoint, token):
    url = endpoint + '/api/auth/logout'
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(url, headers=headers)
    if r.status_code == 204:
        return True
    else:
        print("Portainer logout failed with status code " + str(r.status_code))
        return False

# Portainer get all stacks
#   returns list of stacks, None on failure
def portainer_get_stacks(endpoint, token):
    url = endpoint + '/api/stacks'
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print("Portainer get stacks failed with status code " + str(r.status_code))
        return None

# Portainer get stack file
#   returns stack file, None on failure
def portainer_get_stackfile(endpoint, token, stack_id):
    url = endpoint + '/api/stacks/' + str(stack_id) + '/file'
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.text
    else:
        print("Portainer get stack file failed with status code " + str(r.status_code))
        return None

def backup_portainer(endpoint, username, password, backup_dir):
    # validate args
    if not endpoint.startswith('http'):
        print("Invalid endpoint")
        sys.exit(1)
    if not os.path.isdir(backup_dir):
        print("Invalid output directory")
        sys.exit(1)
    if username == '' or password == '':
        print("Invalid username or password")
        sys.exit(1)

    # login to portainer
    portainer = PortainerClient(endpoint, username, password)
    if not portainer.login():
        sys.exit(1)

    # get all stacks
    stacks = portainer.get_stacks()
    if stacks is None:
        sys.exit(1)

    # get stack files
    for stack in stacks:
        stack_file = portainer.get_stack_file(stack['Id'])
        if stack_file is None:
            print("Failed to get stack file for stack " + stack['Name'])
        with open(os.path.join(backup_dir, stack['Name'] + '.yml'), 'w') as f:
            f.write(stack_file)

    # print success
    print("Successfully backed up " + str(len(stacks)) + " stacks to " + backup_dir)

    # print backed up stacks
    print("Backed up stacks:")
    for stack in stacks:
        print(stack['Name'])

    # logout of portainer
    if not portainer.logout():
        sys.exit(1)

def restore_portainer(endpoint, username, password, backup_dir):
    # validate args
    if not endpoint.startswith('http'):
        print("Invalid endpoint")
        sys.exit(1)
    if not os.path.isdir(backup_dir):
        print("Invalid output directory")
        sys.exit(1)
    if username == '' or password == '':
        print("Invalid username or password")
        sys.exit(1)

    # login to portainer
    portainer = PortainerClient(endpoint, username, password)
    if not portainer.login():
        sys.exit(1)

    # restore stacks
    for stack_file in os.listdir(backup_dir):
        if stack_file.endswith('.yml'):
            stack_name = stack_file[:-4]
            with open(os.path.join(backup_dir, stack_file), 'r') as f:
                if portainer.create_stack(stack_name, f.read()):
                    print("Successfully restored stack " + stack_name)
                else:
                    print("Failed to restore stack " + stack_name)

    # print success
    print("Successfully restored " + str(len(os.listdir(backup_dir))) + " stacks from " + backup_dir)    

def main():
    parser = argparse.ArgumentParser(description='Backup Portainer stacks')
    parser.add_argument('--endpoint', '-e', default='http://localhost:9000',
        help='Portainer endpoint, default http://localhost:9000')
    parser.add_argument('--username', '-u', required=True, help='Portainer username')
    parser.add_argument('--password', '-p', required=True, help='Portainer password')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--restore', '-r', action='store_true', help='Restore stacks')
    args = parser.parse_args()

    # validate args
    if not args.endpoint.startswith('http'):
        print("Invalid endpoint")
        sys.exit(1)
    if not os.path.isdir(args.output):
        print("Invalid output directory")
        sys.exit(1)
    if args.username == '' or args.password == '':
        print("Invalid username or password")
        sys.exit(1)

    # backup or restore
    if args.restore:
        restore_portainer(args.endpoint, args.username, args.password, args.output)
    else:
        backup_portainer(args.endpoint, args.username, args.password, args.output)

if __name__ == "__main__":
    main()

