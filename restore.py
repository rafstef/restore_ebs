#!/usr/bin/env python
#from boto.s3.connection import S3Connection
#from boto.s3.key import Key
#from boto.sqs.message import Message
import boto3
#import re, sys, os, stat, subprocess, json, time, logging
import requests, urllib2, time, json

#sqs = boto.sqs.connect_to_region('us-west-2')
#s3 = boto.connect_s3()
#ec2 = boto.ec2.connect_to_region('us-west-2')
#boto.log.info('Connections made')


create_volume(session,snapshots,az,kms_key):
  volumes = []
  client=boto3.client('ec2')
  for s in snapshots:
    responce=client.create_volume(
      AvailabilityZone=az,
      Encrypted=True,
      KmsKeyId=kms_id,
      VolumeType='gp2',
      TagSpecifications=[
        {
          'Tags':[
            {
	      'Key': 'Name',
	      'Value': TagName,
  	    },
           ]
        },
      ]
    )
    volumes.append(response)
  return volumes

delete_all_volume(instance):     
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



inst_id = urllib2.urlopen("http://169.254.169.254/latest/meta-data/instance-id").read()
response = urllib2.urlopen("http://169.254.169.254/latest/dynamic/instance-identity/document").read()
data = json.loads(response)
region = data["region"]
session = boto3.Session(region_name=region)
ec2 = session.resource('ec2')
instance = ec2.Instance(inst_id)
delete_all_volume(instance)
snapshots=find_snapshots(volume)
