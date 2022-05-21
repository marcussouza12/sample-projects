import json
import os

import boto3
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


def s3_client():
    return boto3.client(
        's3',
        # Hard coded strings as credentials, not recommended.
        aws_access_key_id=settings.get("AWS_ACCESS_KEY"),
        aws_secret_access_key=settings.get("AWS_SECRET_KEY"),
        region_name=settings.get("AWS_REGION")
    )


def s3_resource():
    return boto3.resource(
        's3',
        # Hard coded strings as credentials, not recommended.
        aws_access_key_id=settings.get("AWS_ACCESS_KEY"),
        aws_secret_access_key=settings.get("AWS_SECRET_KEY"),
        region_name=settings.get("AWS_REGION")
    )


def saveFileInS3(self, fileName, filePath, resp):
    if not os.path.exists(filePath):
        os.makedirs(filePath)

    with open(filePath + fileName, 'w') as json_file:
        json.dump(resp, json_file)

    if not self.amazonS3.findFile(filePath, fileName):
        self.amazonS3.upload_file(filePath + fileName)
