# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-02-03 13:49:34
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-02-16 09:32:26
import aws_tools as awt
import time 
import os
import cv2 as cv  
import random as rm
import math

import tkinter as tk 
from PIL import Image, ImageTk

awt.loadKeys("keys.csv")
awt.loadBucket("bucket.txt")

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

mouthBoxRate = 200
targetSpeed = 2
intensity = 100
currentCount = 0
defaultState = 28
stateInd = 28
timeGoing = False
collectFrameMax = 12
collectFrameCount = 12
color = (255,255,255)

stateCounts = [-1,360.0/targetSpeed,-1,360.0/targetSpeed,-1,360.0/targetSpeed] + [-1,mouthBoxRate/targetSpeed]*9 + [-1,-2,-1,-2,1]
stateText = ["Cheek Circle",""]*3 + ["Tongue Out",""]*1 + ["Pucker Lips",""]*2 + ["Left Wink",""]*2 + ["Right Wink",""]*2 + ["Left Brow Raise",""]*2 + ["No Trigger","","Talk In","",""]

def main():
	try:
		loadCircleCenterLoc()
	except Exception as e:
		print("Reverting to Default Circle Location.")
	root = tk.Tk()
	windowX = root.winfo_screenwidth()-900
	windowY = root.winfo_screenheight()-600
	windowXOffset = int(rm.random()*windowX/2)*2
	windowYOffset = int(rm.random()*windowY/2)*2
	root.geometry("900x600+%d+%d"%(windowXOffset,windowYOffset))
	app = Application(master=root)
	app.mainloop()
	
def loadCircleCenterLoc():
	global circleCenter,intensity
	with open("savedLoc.txt","r") as file:
		line = file.readline().replace("\n","").split(",")
		circleCenter = (int(line[0]),int(line[1]))
		intensity = int(line[2])
		
def saveCircleCenterLoc():
	with open("savedLoc.txt","w") as file:
		file.write("%d,%d,%d\n"%(circleCenter[0],circleCenter[1],intensity))
	
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
		
	def packButton(self,text,command,buttonColor="black",side="top",fill="none",parentFrame=None):
		if parentFrame != None:
			newButton = tk.Button(parentFrame)
		else:
			newButton = tk.Button(self)
		newButton["text"] = text
		newButton["fg"] = buttonColor
		newButton["command"] = command
		if fill == "none":
			newButton["width"] = 15
		expand = True if fill != "none" else False
		newButton.pack({"side":side,"fill":fill,"expand":expand})

def runPracticeCycle():
	global state, currentCount,stateInd
	if state == "None":
		state = "Practice"
		currentCount = 0
		stateInd = 0
		generateNewIntensity()
	saveCircleCenterLoc()
	
def runCollectionCycle():
	global state,currentCount,stateInd
	if state == "None":
		state = "Collect"
		currentCount = 0
		stateInd = 0
		generateNewIntensity()
		updateDirectoryName()
	saveCircleCenterLoc()
	
def generateNewCirclePos():
	global state, circleCenter
	if state == "None":
		newX = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*100 + videoWidth/2)
		newY = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*50 + videoHeigh/2) 
		circleCenter = (newX,newY)
		saveCircleCenterLoc()
		
def generateNewIntensity():
	global intensity
	lastIntensity = intensity
	while lastIntensity == intensity:
		intensity = rm.sample([10,50,100],1)[0]
		
def updateImageAndSymbols(parent,imageLabel):
	global collectFrameCount
	ret,image = capture.read()
	imageWithContent,data = drawContent(image)
	placeOpenCVImageInTK(imageWithContent,imageLabel)
	if collectFrameCount == 0 and state == "Collect" and data != {}:
		collectFrameCount = collectFrameMax
		saveImage(image,data)
	if state == "Collect" and data != {}:
		collectFrameCount = collectFrameCount - 1
	
def drawContent(image):
	global targetTime,currentCount,stateInd,state
	imageWithContent = image.copy()
	targetLocation = (0,0)
	
	updateStateAndTimeInfo()
	
	if state != "None":
		currentCount,stateInd = controlStateGetCount(stateInd,currentCount)
	
	radius = getRadius(stateInd)
	
	if stateInd <= 5 or stateInd == defaultState:
		drawMouthCircles(imageWithContent,radius)
		if stateInd%2==1:
			targetLocation = drawTargetCircles(imageWithContent,radius,currentCount)
	
	if stateInd%2 == 1 and stateInd >5 and stateInd <=23:
		drawTargetBox(imageWithContent,currentCount)
	imageWithContent = cv.flip(imageWithContent,1)
	if stateInd%2 == 0 and stateInd != defaultState:
		drawCountDown(imageWithContent,targetTime,stateText[stateInd])
		data = {}
	else:
		data = makeDataDict(targetLocation,getStateName(stateInd),currentCount,stateCounts[stateInd])
	
	if stateInd == defaultState:
		if state == "Collect":
			awt.uploadDirectoryWithWindow(directory)
		state = "None"
		currentCount = 0
		
	drawIntensity(imageWithContent)
	return imageWithContent,data
	
def placeOpenCVImageInTK(image,label_image):
	image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
	tkimg[0] = ImageTk.PhotoImage(Image.fromarray(image))
	label_image.config(image=tkimg[0])
	
def updateStateAndTimeInfo():
	global targetTime,timeGoing,stateInd
	if targetTime < time.time():
		if timeGoing == True:
			stateInd = stateInd + 1
			timeGoing = False
			if stateInd == 25 or stateInd == 27:
				targetTime, timeGoing = getTargetTime(stateInd)
				
		elif stateInd%2==0 and stateInd != defaultState:
			targetTime, timeGoing = getTargetTime(stateInd)

def controlStateGetCount(stateInd,currentCount):
	if stateCounts[stateInd] < 0:
		return currentCount, stateInd
	elif currentCount >= stateCounts[stateInd]:
		return 0,stateInd+1
	else:
		return currentCount + 1,stateInd
		
def getTargetTime(stateInd):
	if stateCounts[stateInd] == -1:
		return time.time() + 5, True
	elif stateCounts[stateInd] == -2:
		return time.time() + 2, True
	else:
		return time.time() -1, False
		
def getStateName(stateInd):
	if stateInd <= 5:
		return "In Cheek"
	elif stateInd > 5 and stateInd <= 7:
		return "Tongue Out"
	elif stateInd > 7 and stateInd <= 11:
		return "Pucker Lips"
	elif stateInd > 11 and stateInd <= 15:
		return "Left Wink"
	elif stateInd > 15 and stateInd <= 19:
		return "Right Wink"
	elif stateInd > 19 and stateInd <= 23:
		return "Left Brow"
	elif stateInd > 23 and stateInd <= 25:
		return "No Trigger"
	elif stateInd > 25 and stateInd <= 27:
		return "Talking"
		
def getRadius(stateInd):
	if stateInd <= 1 or stateInd == defaultState:
		return mainRadius 
	if stateInd <= 3 and stateInd > 1:
		return mainRadius - 20
	if stateInd <= 5 and stateInd > 3:
		return mainRadius - 40		
		
def drawMouthCircles(image,radius):
	cv.circle(image,circleCenter,radius,(255,255,255),2)
	cv.circle(image,circleCenter,2,(255,255,255),2)

def drawTargetCircles(image,radius,circleLoopNumber):
	xPos = int(math.cos(targetSpeed*math.pi*(circleLoopNumber)/180.0 - math.pi/4)*radius) + circleCenter[0]
	yPos = int(math.sin(targetSpeed*math.pi*(circleLoopNumber)/180.0 - math.pi/4)*radius) + circleCenter[1]
	cv.circle(image,(xPos,yPos),10,(255,100,30),2)
	return (xPos,yPos)
	
def drawTargetBox(image,boxLoopNumber):
	xDiff = 50 - abs(int((boxLoopNumber*targetSpeed/mouthBoxRate)*100)%100 - 50)
	yDiff = 25 - abs(int((boxLoopNumber*targetSpeed/mouthBoxRate)*50)%50 - 25)
	boxColor = (abs(int((boxLoopNumber*targetSpeed/mouthBoxRate)*510)%510 - 255),0,255 - abs(int((boxLoopNumber*targetSpeed/mouthBoxRate)*510)%510 - 255))
	cv.rectangle(image,(circleCenter[0]-xDiff,circleCenter[1] - yDiff),(circleCenter[0]+xDiff,circleCenter[1] +yDiff),boxColor,3)
	
def drawCountDown(image,targetTime,modeText):
	number = max(int(targetTime - time.time()),0)
	font = cv.FONT_HERSHEY_SIMPLEX
	bottomLeftCornerOfText = (circleCenter[0]-40,circleCenter[1]+40)
	fontScale = 4
	lineType = 9
	cv.putText(image,modeText,(50,100),font, 2,color,7)
	cv.putText(image,"%d"%(number+1), bottomLeftCornerOfText, font, fontScale,color,lineType)
	
def drawIntensity(image):
	global color
	color = (0,0,255)
	if intensity == 10:
		color = (30,255,0)
	if intensity == 50:
		color = (0,190,190)
	cv.putText(image,"Intensity", (20,410), cv.FONT_HERSHEY_SIMPLEX, 1,color,3)
	cv.putText(image,"%d"%intensity, (20,450), cv.FONT_HERSHEY_SIMPLEX, 1,color,3)
	
def makeDataDict(target,cycleState,stepNumber,totalSteps):
	data = {}
	data["name"] = "%r"%time.time()+".png"
	data["targetX"] = "%d"%target[0]
	data["targetY"] = "%d"%target[1]
	data["targetIntensity"] = "%d"%intensity
	data["state"] = cycleState
	data["stepNumber"] = "%d"%stepNumber
	data["totalSteps"] = "%d"%totalSteps
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
	output = output + data["stepNumber"]+","
	output = output + data["totalSteps"]+","
	output = output + data["state"]+"\n"
	file.write("%s"%(output))
	
if __name__ == '__main__':
	main()

