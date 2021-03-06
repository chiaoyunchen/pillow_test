import os, sys

from PIL import Image
from boto3.s3.transfer import S3Transfer

import boto3
import uuid
import subprocess

s3_client = boto3.client('s3')
transfer = S3Transfer(s3_client)
thumb_size = 200, 200


def resize_image(image_path, resized_path):
    with Image.open(image_path) as image:
        image.thumbnail(thumb_size)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(resized_path)


def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        rand = uuid.uuid4()
        download_path = '/tmp/{}'.format(rand)
        upload_path = 'thumb-{}.jpg'.format(rand)

        response = s3_client.head_object(Bucket=bucket, Key=key)
        type = response['ContentType']

        if type in ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']:
          transfer.download_file(bucket, key, download_path)
          resize_image(download_path, upload_path)

          if type not in ['image/jpg', 'image/jpeg']:
              key = key+".jpeg"
          transfer.upload_file(upload_path, '{}-thumbs'.format(bucket), key, extra_args={'ContentType': 'image/jpeg'})
          continue

        if type in ['video/mp4']:
          transfer.download_file(bucket, key, download_path)
          cmd = './ffmpeg -i "{}" -ss 00:00:00 -vframes 1 -vf "scale=200:200:force_original_aspect_ratio=increase,crop=200:200" {}'.format(download_path, upload_path)
          subprocess.call(cmd, shell=True)

          transfer.upload_file(upload_path, '{}-thumbs'.format(bucket), key+".jpeg", extra_args={'ContentType': 'image/jpeg'})
          continue

        print(type, 'is not supported')
