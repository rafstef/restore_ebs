#!/usr/bin/env python

import boto3
import requests
import re
import getopt
import sys
import urllib2
import time
import json
import socket

ENV="PRD"



import logging as log
log.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                level=log.INFO,
                datefmt='%m/%d/%Y %H:%M:%S')

def snapshot_get_tag(snapshot, tag_name, default=None):
    tags = dict(map(lambda x: (x['Key'], x['Value']), snapshot.tags or []))
    return tags.get(tag_name, default)

def delete_all_volume(ec2,instance):
  for v in instance.block_device_mappings:
    if v['DeviceName']==instance.root_device_name: 
      continue
    print(v['DeviceName'])
    print(v['Ebs']['VolumeId'])
    volume = ec2.Volume(v['Ebs']['VolumeId'])
    print("Detach volume %s", volume.id)
    instance.detach_volume(VolumeId=(v['Ebs']['VolumeId']))
    while volume.state != 'available':
      time.sleep(10)
      volume.reload()
      volume.state
    print("Delete volume %s", volume.id)
    volume.delete()

def find_snapshots(f):
  client=boto3.client('ec2')
  r = client.describe_snapshots(Filters=f)
  return r

def order_snapshots(snapshots):
   return sorted(snapshots, key=lambda k: k['StartTime'], reverse=True)

def create_filter(hostname, env):
  f = '%s_%s_*' % (hostname.upper(), env.upper())
  snapshots_filter = [{'Name': 'tag:Name', 'Values': [f]}]
  return snapshots_filter

def snapshots_to_restore(ordered_snapshots):
  volume_ids =[]
  snapshots_to_restore = []
  for s in (ordered_snapshots):
    if s['VolumeId'] not in volume_ids:
      volume_ids.append(s['VolumeId'])
      snapshots_to_restore.append(s)
  return snapshots_to_restore


def last_snapshots(service_groups,snapshots):
  snapshot_to_restore =[]
  for sg in service_groups:
    for s in snapshots:
      if( s["Tags"][0]['Key'] == 'Name' ) and ( s["Tags"][0]['Value'].split("_")[2] == sg ):
	snapshot_to_restore.add(s)		
  return snasphot_to_restore   

def create_volumes(ec2,snapshots,az):
  volumes=[]
  for s in snapshots:
    try: 
      volume = ec2.create_volume(
        SnapshotId=s['SnapshotId'],
        AvailabilityZone=az,
        VolumeType="gp2",
        TagSpecifications=[
            {
              'ResourceType': 'volume',
              'Tags': [
                  {
                      'Key': 'Name',
                      'Value': s['Description']
                  },
              ]
          },
        ]    
      )
    except Exception as e:
      raise e
      system.exit(2)
    log.info(volume.state)
    state = volume.state
    while(state != "available"):
      time.sleep(1)
      volume.reload()
      state = volume.state 
    log.info("volume %s available" % volume.id)   
    volumes.append(volume)
  return volumes

def attach_volumes(volumes,instance):
  client=boto3.client('ec2')
  n = 0
  devs = [devicename["DeviceName"] for devicename in instance.block_device_mappings]
  tmp_devs = [re.sub(r'.*([a-z]{3,})[0-9]*', '\g<1>', s)
                for s in devs]
  used_devs = set(tmp_devs)
  free_devs = ['sd'+c for c in string.ascii_lowercase[5:]]
  free_devs = list(set(free_devs) - used_devs)
  free_devs.sort()
  log.info("free device %s" % free_devs)
  for v in volumes:
    print v    
    try:
      response = client.attach_volume(
        InstanceId=str(instance.id),
        Device = free_devs[n],
        VolumeId=v.id
      )
    except Exception as e:
      raise e
      system.exit(2)
    n = n + 1
    if n > len(free_devs):
      print("Not enough devices")
      system.exit(1)  

def main():
  #hostname = socket.gethostname()
  hostname = "TCCAUSV1APL-EDICORE01"
  log.info("%s", hostname)
  inst_id = urllib2.urlopen("http://169.254.169.254/latest/meta-data/instance-id").read()
  response = urllib2.urlopen("http://169.254.169.254/latest/dynamic/instance-identity/document").read()
  data = json.loads(response)
  region = data["region"]
  session = boto3.Session(region_name=region)
  ec2 = session.resource('ec2')
  instance = ec2.Instance(inst_id)
  f = create_filter(hostname,ENV)
  #find snapshots of vm
  snapshots = find_snapshots(f)
  log.info("snapshots: %s  \n\n\n" %  snapshots)
  #order snapshots
  ordered_snapshots=order_snapshots(snapshots['Snapshots'])
  log.info("ordered_snapshots: %s \n\n\n " %  ordered_snapshots)
  s_to_restore = snapshots_to_restore(ordered_snapshots)
  log.info("s_to_restore:  %s \n\n\n " %  s_to_restore) 
  az = urllib2.urlopen("http://169.254.169.254/latest/meta-data/placement/availability-zone").read()
  volumes = create_volumes(ec2,s_to_restore,az)
  delete_all_volume(ec2,instance)
  attach_volumes(volumes, instance) 

if __name__ == '__main__':
  main()
