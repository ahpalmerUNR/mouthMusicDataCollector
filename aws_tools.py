# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-02-03 13:59:13
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-02-10 14:37:12
from os import listdir
from os.path import isfile, join

import boto3
import tkinter as tk
from tkinter.ttk import Progressbar

accessKey = ''
secretKey = ''
bucketName = ''

def awsSession(region_name='us-west-2'):
	return boto3.session.Session(aws_access_key_id=accessKey,
								aws_secret_access_key=secretKey,
								region_name=region_name)

def uploadDirectoryWithWindow(directory):
	onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]
	root = tk.Tk()
	root.geometry("900x40")
	app = tk.Frame(master=root)
	app.winfo_toplevel().title("Mouth Music Data Gatherer Upload Progress")
	progress = tk.IntVar()
	bar = Progressbar(app,orient="horizontal",length=900,mode="determinate",maximum=len(onlyfiles),variable=progress)
	bar.pack()
	app.pack()
	for a in range(len(onlyfiles)):
		uploadFileToAws(directory + onlyfiles[a],directory + onlyfiles[a])
		bar.step(1)
		root.update_idletasks()
		root.update()
	

def uploadDirectoryToAWS(directory):
	onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]
	for a in onlyfiles:
		uploadFileToAws(directory + a,directory + a)

def uploadFileToAws(localFile, s3File):
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
	
def loadBucket(bucketFilePath):
	global bucketName
	with open(bucketFilePath,"r") as file:
		bucketName = file.readline().replace("\n","")