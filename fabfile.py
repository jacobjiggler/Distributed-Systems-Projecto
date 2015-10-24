from fabric.api import *
from fabric.contrib.project import rsync_project

env.user = 'ec2-user'

with open('ip', 'r') as f:
    env.hosts = f.read().splitlines()

def deploy():
    rsync_project(local_dir='.', remote_dir='code', exclude='env')

    host_id = env.hosts.index(env.host_string)
    with cd('code'):
        run('python node.py {} --nocli'.format(host_id))
