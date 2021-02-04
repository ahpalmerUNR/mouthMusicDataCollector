# -*- coding: utf-8 -*-
# @Author: ahpalmerUNR
# @Date:   2021-02-03 13:49:34
# @Last Modified by:   ahpalmerUNR
# @Last Modified time: 2021-02-04 14:02:44
import aws_tools as awt
import time 
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

tkimg = [None]
state = "None"
circleCenter = (int(videoWidth/2),int(videoHeigh/2))
mainRadius = 90
targetTime = time.time()

circleLoopNumber = 0
mouthBoxRate = 200
targetSpeed = 2

def main():
	root = tk.Tk()
	root.geometry("900x600")
	app = Application(master=root)
	app.mainloop()
	
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
			parent.master.after(15,lambda:updateImage(parent,label))
			
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
	
def runCollectionCycle():
	global state
	if state == "None":
		state = "Collect"
	
def generateNewCirclePos():
	global state, circleCenter
	if state == "None":
		newX = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*100 + videoWidth/2)
		newY = int(rm.random()*((-1)**(math.floor(rm.random()+.5)))*50 + videoHeigh/2) 
		print(newX,newY,-1**(math.floor(rm.random()+.5)))
		circleCenter = (newX,newY)
		
def updateImageAndSymbols(parent,imageLabel):
	ret,image = capture.read()
	imageWithContent,data = drawContent(image)
	placeOpenCVImageInTK(imageWithContent,imageLabel)
	saveImage(image,data)
	
def drawContent(image):
	global circleLoopNumber,targetTime
	imageWithContent = image.copy()
	if circleLoopNumber%1000 == 0:
		targetTime = time.time() + 4
	circleLoopNumber = circleLoopNumber + 2
	drawMouthCircles(imageWithContent,mainRadius)
	drawTargetCircles(imageWithContent,mainRadius,circleLoopNumber)
	drawTargetBox(imageWithContent,circleLoopNumber)
	drawCountDown(imageWithContent,targetTime)
	return imageWithContent,0
	
def placeOpenCVImageInTK(image,label_image):
	image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
	tkimg[0] = ImageTk.PhotoImage(Image.fromarray(image))
	label_image.config(image=tkimg[0])

def saveImage(image,data):
	pass
	
def drawMouthCircles(image,radius):
	cv.circle(image,circleCenter,radius,(255,255,255),2)
	cv.circle(image,circleCenter,2,(255,255,255),2)

def drawTargetCircles(image,radius,circleLoopNumber):
	xPos = int(math.cos(targetSpeed*math.pi*circleLoopNumber/360.0)*radius) + circleCenter[0]
	yPos = int(math.sin(targetSpeed*math.pi*circleLoopNumber/360.0)*radius) + circleCenter[1]
	cv.circle(image,(xPos,yPos),10,(255,100,30),2)
	
def drawTargetBox(image,boxLoopNumber):
	xDiff = 50 - abs(int((boxLoopNumber/mouthBoxRate)*100)%100 - 50)
	yDiff = 25 - abs(int((boxLoopNumber/mouthBoxRate)*50)%50 - 25)
	color = (abs(int((boxLoopNumber/mouthBoxRate)*510)%510 - 255),0,255 - abs(int((boxLoopNumber/mouthBoxRate)*510)%510 - 255))
	cv.rectangle(image,(circleCenter[0]-xDiff,circleCenter[1] - yDiff),(circleCenter[0]+xDiff,circleCenter[1] +yDiff),color,3)
	
def drawCountDown(image,targetTime):
	number = max(int(targetTime - time.time()),0)
	font = cv.FONT_HERSHEY_SIMPLEX
	bottomLeftCornerOfText = (10,50)
	fontScale = 1
	fontColor = (0,0,255)
	lineType = 2

	cv.putText(image,"%d"%number, bottomLeftCornerOfText, font, fontScale,fontColor,lineType)


if __name__ == '__main__':
	main()

