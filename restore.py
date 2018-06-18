#!/usr/bin/env python
#from boto.s3.connection import S3Connection
#from boto.s3.key import Key
#from boto.sqs.message import Message
import boto3
#import re, sys, os, stat, subprocess, json, time, logging
import getopt, sys, pprint,requests, urllib2, time, json, socket

ENV="PRD"



'''
- trovare tutti gli snapshots che hanno tag name iniziante con hostname
hostname_prd_******

- filtro env nel name
- dei volumi con nome uguale prendo l'ultimo generato
- creo volumi
- attach volume
'''

def snapshot_get_tag(snapshot, tag_name, default=None):
    tags = dict(map(lambda x: (x['Key'], x['Value']), snapshot.tags or []))
    return tags.get(tag_name, default)

def delete_all_volume(instance):
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

def main():
  #hostname = socket.gethostname()
  hostname = "TCCAUSV1APL-EDICORE01"
  print(hostname)
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
  #order snapshots
  ordered_snapshots=order_snapshots(snapshots['Snapshots'])
  s_to_restore = snapshots_to_restore(ordered_snapshots)
  print(s_to_restore) 
  
   
 
  #delete_all_volume(instance)
  #snapshots=find_snapshots(hostname)

if __name__ == '__main__':
  main()
