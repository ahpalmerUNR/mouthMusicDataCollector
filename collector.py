# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-02-03 13:49:34
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-02-08 16:11:42
import aws_tools as awt
import time 
import os
import cv2 as cv 
import numpy as np 
import random as rm
import math

import tkinter as tk 
from PIL import Image, ImageTk

awt.loadKeys("keys.csv")

videoWidth, videoHeigh = (640,480)
capture = cv.VideoCapture(0)
capture.set(3,videoWidth)
capture.set(4,videoHeigh)

directory = ""

tkimg = [None]
state = "None"
circleCenter = (int(videoWidth/2),int(videoHeigh/2))
mainRadius = 90
targetTime = time.time()

circleLoopNumber = 0
mouthBoxRate = 200
targetSpeed = 2
intensity = 100
currentCount = 0
stateInd = 0

stateCounts = [-1,360.0/targetSpeed,-1,360.0/targetSpeed,-1,360.0/targetSpeed] + [-1,mouthBoxRate,-1,mouthBoxRate,-1,mouthBoxRate]*5 + [-1,-2,-1,-2,0]
stateText = ["Cheek Circle",""]*3 + ["Tongue Out",""]*3 + ["Pucker Lips",""]*3 + ["Left Wink",""]*3 + ["Right Wink",""]*3 + ["Left Brow Raise",""]*3 + ["Stay Still","","Talk In","",""]

def main():
	try:
		loadCircleCenterLoc()
	except Exception as e:
		print("Reverting to Default Circle Location.")
	root = tk.Tk()
	root.geometry("900x600")
	app = Application(master=root)
	app.mainloop()
	
def loadCircleCenterLoc():
	global circleCenter
	with open("savedLoc.txt","r") as file:
		line = file.readline().replace("\n","").split(",")
		circleCenter = (int(line[0]),int(line[1]))
		
def saveCircleCenterLoc():
	with open("savedLoc.txt","w") as file:
		file.write("%d,%d\n"%(circleCenter[0],circleCenter[1]))
	
class Application(tk.Frame):
	"""Application Window"""
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.pack({"fill":"both","expand":True})
		self.drawHome()
		self.winfo_toplevel().title("Mouth Music Data Gatherer")
		
	def drawHome(self):
		imageTKLabel = tk.Label(self)
		imageTKLabel.pack()
					
		def updateImage(parent,label):
			updateImageAndSymbols(parent,label)
			parent.master.update_idletasks()
			parent.master.after(5,lambda:updateImage(parent,label))
			
		updateImage(self,imageTKLabel)
		self.packButton("Practice",runPracticeCycle,side="left",fill="x")
		self.packButton("Collect",runCollectionCycle,side="left",fill="x")
		self.packButton("New Position",generateNewCirclePos,side="right",fill="x")
		
	def packButton(self,text,command,color="black",side="top",fill="none",parentFrame=None):
		if parentFrame != None:
			newButton = tk.Button(parentFrame)
		else:
			newButton = tk.Button(self)
		newButton["text"] = text
		newButton["fg"] = color
		newButton["command"] = command
		if fill == "none":
			newButton["width"] = 15
		expand = True if fill != "none" else False
		newButton.pack({"side":side,"fill":fill,"expand":expand})

def runPracticeCycle():
	global state
	if state == "None":
		state = "Practice"
	generateNewIntensity()
	
def runCollectionCycle():
	global state
	if state == "None":
		state = "Collect"
	generateNewIntensity()
	updateDirectoryName()
	
def generateNewCirclePos():
	global state, circleCenter
	if state == "None":
		newX = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*100 + videoWidth/2)
		newY = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*50 + videoHeigh/2) 
		circleCenter = (newX,newY)
		saveCircleCenterLoc()
		
def generateNewIntensity():
	global intensity
	intensity = rm.sample([10,50,100],1)[0]
		
def updateImageAndSymbols(parent,imageLabel):
	ret,image = capture.read()
	imageWithContent,data = drawContent(image)
	placeOpenCVImageInTK(imageWithContent,imageLabel)
	if int(time.time())%2 == 0 and state == "Collect" and data != {}:
		saveImage(image,data)
	
def drawContent(image):
	global circleLoopNumber,targetTime,currentCount,stateInd,state
	
	imageWithContent = image.copy()
	targetLocation = (0,0)
	if targetTime < time.time():
		targetTime = getTargetTime(stateInd)
	if state != "None":
		currentCount,stateInd = controlStateGetCount(stateInd,currentCount)
	if stateInd <= 1:
		radius = mainRadius 
	if stateInd <= 3 and stateInd > 1:
		radius = mainRadius - 30
	if stateInd <= 5 and stateInd > 3:
		radius = mainRadius - 60
	if stateInd <= 5:
		drawMouthCircles(imageWithContent,radius)
		if stateInd%2==1:
			targetLocation = drawTargetCircles(imageWithContent,radius,circleLoopNumber)
	if stateInd%2 == 1 and stateInd >5 and stateInd <=35:
		drawTargetBox(imageWithContent,circleLoopNumber)
	if stateInd%2 == 0:
		drawCountDown(imageWithContent,targetTime,stateText[stateInd])
		data = {}
	else:
		data = makeDataDict(targetLocation,getStateName(stateInd))
	if stateInd == 47 and currentCount == stateCounts[stateInd]:
		state = "None"
		stateInd = 0
		currentCount = 0
	return imageWithContent,data
	
def placeOpenCVImageInTK(image,label_image):
	image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
	tkimg[0] = ImageTk.PhotoImage(Image.fromarray(image))
	label_image.config(image=tkimg[0])

def controlStateGetCount(stateInd,currentCount):
	if stateCounts[stateInd] < 0:
		return currentCount, stateInd
	elif currentCount >= stateCounts[stateInd]:
		return 0,stateInd+1
	else:
		return currentCount + 1,stateInd
		
def getTargetTime(stateInd):
	if stateCounts[stateInd] == -1:
		return time.time() + 4
	elif stateCounts[stateInd] == -2:
		return time.time() + 2
	else:
		return time.time() -1
		
def getStateName(stateInd):
	if stateInd <= 5:
		return "In Cheek"
	elif stateInd > 5 and stateInd <= 11:
		return "Tongue Out"
	elif stateInd > 11 and stateInd <= 17:
		return "Pucker Lips"
	elif stateInd > 17 and stateInd <= 23:
		return "Left Wink"
	elif stateInd > 23 and stateInd <= 29:
		return "Right Wink"
	elif stateInd > 29 and stateInd <= 35:
		return "Left Brow"
	elif stateInd > 35 and stateInd <= 41:
		return "No Trigger"
	elif stateInd > 41 and stateInd <= 47:
		return "Talking"
		
def drawMouthCircles(image,radius):
	cv.circle(image,circleCenter,radius,(255,255,255),2)
	cv.circle(image,circleCenter,2,(255,255,255),2)

def drawTargetCircles(image,radius,circleLoopNumber):
	xPos = int(math.cos(targetSpeed*math.pi*circleLoopNumber/360.0)*radius) + circleCenter[0]
	yPos = int(math.sin(targetSpeed*math.pi*circleLoopNumber/360.0)*radius) + circleCenter[1]
	cv.circle(image,(xPos,yPos),10,(255,100,30),2)
	return (xPos,yPos)
	
def drawTargetBox(image,boxLoopNumber):
	xDiff = 50 - abs(int((boxLoopNumber/mouthBoxRate)*100)%100 - 50)
	yDiff = 25 - abs(int((boxLoopNumber/mouthBoxRate)*50)%50 - 25)
	color = (abs(int((boxLoopNumber/mouthBoxRate)*510)%510 - 255),0,255 - abs(int((boxLoopNumber/mouthBoxRate)*510)%510 - 255))
	cv.rectangle(image,(circleCenter[0]-xDiff,circleCenter[1] - yDiff),(circleCenter[0]+xDiff,circleCenter[1] +yDiff),color,3)
	
def drawCountDown(image,targetTime,modeText):
	number = max(int(targetTime - time.time()),0)
	font = cv.FONT_HERSHEY_SIMPLEX
	bottomLeftCornerOfText = (circleCenter[0]-40,circleCenter[1]+40)
	fontScale = 4
	fontColor = (0,0,255)
	lineType = 9
	cv.putText(image,modeText,(50,100),font, 2,(200,0,150),lineType)
	cv.putText(image,"%d"%number, bottomLeftCornerOfText, font, fontScale,fontColor,lineType)
	
def makeDataDict(target,cycleState):
	data = {}
	data["name"] = "%r"%time.time()+".png"
	data["targetX"] = "%d"%target[0]
	data["targetY"] = "%d"%target[1]
	data["targetIntensity"] = "%d"%intensity
	data["state"] = cycleState
	return data
	
def updateDirectoryName():
	global directory
	directory = time.strftime("%d-%b-%Y-%H-%M-%S/", time.localtime())
	os.mkdir("./"+directory)
	
def saveImage(image,data):
	cv.imwrite(directory + data["name"],image)
	with open(directory+"data.txt","a") as file:
		writeData(file,data)

def writeData(file,data):
	output = data["name"]+","
	output = output + data["targetX"]+","
	output = output + data["targetY"]+","
	output = output + data["targetIntensity"]+","
	output = output + data["state"]+"\n"
	file.write("%s"%(output))
	


if __name__ == '__main__':
	main()

