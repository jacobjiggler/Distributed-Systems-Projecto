from fabric.api import *
from fabric.contrib.project import rsync_project

env.user = 'ec2-user'

with open('ip', 'r') as f:
    env.hosts = f.readlines()

def deploy():
    rsync_project(local_dir='.', remote_dir='code', exclude='env')
