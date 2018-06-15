#!/usr/bin/env python
#from boto.s3.connection import S3Connection
#from boto.s3.key import Key
#from boto.sqs.message import Message
import boto3
#import re, sys, os, stat, subprocess, json, time, logging
import pprint,requests, urllib2, time, json, socket

# #sqs = boto.sqs.connect_to_region('us-west-2')
# #s3 = boto.connect_s3()
# #ec2 = boto.ec2.connect_to_region('us-west-2')
# #boto.log.info('Connections made')
# def create_volume(session,snapshots,az,kms_key):
#   volumes = []
#   client=boto3.client('ec2')
#   for s in snapshots:
#     responce=client.create_volume(
#       AvailabilityZone=az,
#       Encrypted=True,
#       KmsKeyId=kms_id,
#       VolumeType='gp2',
#       TagSpecifications=[
#         {
#           'Tags':[
#             {
# 	      'Key': 'Name',
# 	      'Value': TagName,
#   	    },
#            ]
#         },
#       ]
#     )
#     volumes.append(response)
#   return volumes

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

def find_last_snapshot(snapshots):
   sorted(list_to_be_sorted, key=lambda k: k['date'], reverse=True)[0]


def create_filter(hostname, env):
  f = '%s_%s_*' % (hostname.upper(), env.upper())
  snapshots_filter = [{'Name': 'tag:Name', 'Values': [f]}]
  return snapshots_filter

def snapshot_service_groups(snapshots):
  service_groups = []
  for s in snapshots:
    if s["Tags"][0]['Key'] == 'Name':
      sg = s["Tags"][0]['Value'].split("_")[2]
      if sg not in service_groups:
        service_groups.append(sg) 
  return service_groups      

def last_snapshots(service_groups,snapshots):
  snapshot_to_restore =[]
  for sg in service_groups:
    for s in snapshots:
      if s["Tags"][0]['Key'] == 'Name' and s["Tags"][0]['Value'].split("_")[2] == sg
      

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
  f = create_filter(hostname,"PRD")
  snapshots = find_snapshots(f)
  service_group = snapshot_service_groups(snapshots['Snapshots'])
  
 
  #delete_all_volume(instance)
  #snapshots=find_snapshots(hostname)

if __name__ == '__main__':
  main()
