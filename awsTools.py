# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-02-03 13:59:13
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-02-03 16:31:35
import boto3
from botocore.exceptions import NoCredentialsError

accessKey = ''
secretKey = ''

def awsSession(region_name='us-west-2'):
	return boto3.session.Session(aws_access_key_id=accessKey,
								aws_secret_access_key=secretKey,
								region_name=region_name)

def uploadToAws(localFile, bucketName, s3File):
	session = awsSession()
	s3_resource = session.resource('s3')

	bucket = s3_resource.Bucket(bucketName)
	bucket.upload_file(Filename=localFile,Key=localFile,ExtraArgs={'ACL': 'public-read'})

	s3Url = "https://%s.s3.amazonaws.com/%s"%(bucketName,localFile)
	return s3Url
		
def loadKeys(keyFilePath):
	global accessKey,secretKey
	with open(keyFilePath,"r") as file:
		dictKeys = file.readline().replace("\r\n","").split(",")
		dictValues = file.readline().replace("\r\n","").split(",")
	accessControlDict = dict(zip(dictKeys,dictValues))
	accessKey = accessControlDict["Access key ID"]
	secretKey = accessControlDict["Secret access key"]