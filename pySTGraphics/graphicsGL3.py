import sys#, pygame
import os
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import collections
import logging
import decimal
D = decimal.Decimal
import xml.etree.ElementTree as ET
import re
from operator import itemgetter

import pySTGraphics.glfw as glfw
import pySTGraphics.OpenGL3lib as OpenGL3lib
import pySTGraphics.fonts as fonts
import pySTGraphics.conversionFunctions as conversionFunctions

import pyxpudpserver as XPUDP

## @package Graphics module. Collection of high level graphics objects 


if getattr(sys, 'frozen', False):
	# we are running in a bundle
	working_dir = sys._MEIPASS
else:
	working_dir = os.getcwd()
    
#working_dir = os.path.dirname(os.path.abspath(__file__))

#--------------------------------------------------------------------------------------------------------------------
# TEXT FORMATTING PATTERNS
#--------------------------------------------------------------------------------------------------------------------
TXT_FMT_3DIG_PREC0_0PADDED = '{:03.0f}'
TXT_FMT_3DIG_PREC2 = '{:06.2f}'
TXT_FMT_3DIG_PREC3 = '{:07.3f}'

def parseTextCoordinates(textCoordinates):
    outCoordinates =[0,0]
    #get rid of brackets
    textCoordinates = textCoordinates.replace('[','')
    textCoordinates = textCoordinates.replace(']','')
    
    textCoordinatesSplit = textCoordinates.split(',')
    
    outCoordinates[0] = float(textCoordinatesSplit[0])
    outCoordinates[1] = float(textCoordinatesSplit[1])
    
    return outCoordinates

## parses a string of points in format [x1,y1],[x2,y2],...[xn,yn] and returns a list of points sorted by their x value in format [[x float1,y float1], ...[x floatn,y floatn]]
# @param pointsString 	the string of points to parse
#
def returnPointsList(pointsString):
    pointsList = []
    logging.debug('Points list string: '+pointsString)
    pointsStringList = re.findall('\[[ -]*?[0-9]+.*?[0-9]*?[,]+[ -]*?[0-9]+.*?[0-9]*?[ ]*?\]',
                                    pointsString)	# find all points format [nr,nr]

    for pointString in pointsStringList:
        pointString = re.sub('[\[\] ]+', '', pointString)	#strip spaces, [ and ]
        #print("interval string stripped of []: ", pointString)

        valueStrings = pointString.split(',')

        if len(valueStrings) == 2:
            #print("valueStrings: ", valueStrings)
            pointsList.append([ float(valueStrings[0]), float(valueStrings[1])])

    # let's order the table by ascending x of each pointString

    pointsList.sort(key=itemgetter(0))


    return pointsList

class PanelFileConfig(object):
    
    def __init__(self, XMLconfigFilePath):
        self.XMLconfigFilePath = XMLconfigFilePath
        self.configFileLoaded = False
        if  XMLconfigFilePath != None:
            try:
                self.tree = ET.parse(self.XMLconfigFilePath)
                self.root = self.tree.getroot()
                if self.root.tag == "Container":
                    self.configFileLoaded = True
                else:
                    logging.warning('Root tag incorrect, can not load configuration file, will continue with default values and empty container')
            except:
                logging.error('Error while loading container config file', exc_info=True)
                self.configFileLoaded = False
    
    def createConfigFile(self, XMLconfigFile):
        config_file = open(XMLconfigFile, "w")
        config_file.write("<Container></Container>")
        config_file.close()
    
    def getPanelConfig(self):
        # some default values
        if self.configFileLoaded == False:
            panelConfigDict = {
                            'position': [0,0],
                            'size': [640,480],
                            'name': 'name'
                            }
        if self.configFileLoaded == True:
            panelConfigDict = {
                            'position': parseTextCoordinates(self.root.attrib['position']),
                            'size': parseTextCoordinates(self.root.attrib['size']),
                            'name': self.root.attrib['name']
                            }
        return panelConfigDict
        
    def getComponents(self):
        if self.configFileLoaded == True:
            itemListConfig = []
            
            for child in self.root:
                logging.debug(child.tag, child.attrib)
                
                maintainProportions = True
                if child.attrib['maintainProportions'] == "False":
                    maintainProportions = False
                
                resizeToContainer = True
                if child.attrib['resizeToContainer'] == "False":
                    resizeToContainer = False
                    
                itemListConfig.append ( {
                                        'containerType': child.tag,
                                        'texture': os.path.join(working_dir,child.attrib['texture']), 
                                        'layer': int(child.attrib['layer']), 
                                        'position': parseTextCoordinates(child.attrib['position']), 
                                        'cliprect': parseTextCoordinates(child.attrib['cliprect']),
                                        'origin': parseTextCoordinates(child.attrib['origin']),
                                        'name': child.attrib['name'],
                                        'maintainProportions': maintainProportions,
                                        'resizeToContainer' : resizeToContainer
                                        })
            return itemListConfig
        else :
            return []
    
    def getComponentConfig(self, componentName):
        if self.configFileLoaded == True:
            logging.debug("trying to find comp tag for component: %s", componentName)
            compTags = self.root.findall(".//*[@name='"+componentName+"']")
            
            if len(compTags) > 0:
                compTag = compTags[0]
                logging.debug ("found component, name: %s", compTag.attrib['name'])
                
                maintainProportions = True
                if compTag.attrib['maintainProportions'] == "False":
                    maintainProportions = False
                
                resizeToContainer = True
                if compTag.attrib['resizeToContainer'] == "False":
                    resizeToContainer = False
                    
                componentConfig = {
                                        'containerType': compTag.tag,
                                        'texture': os.path.join(working_dir,compTag.attrib['texture']), 
                                        'layer': int(compTag.attrib['layer']), 
                                        'position': parseTextCoordinates(compTag.attrib['position']), 
                                        'cliprect': parseTextCoordinates(compTag.attrib['cliprect']),
                                        'origin': parseTextCoordinates(compTag.attrib['origin']),
                                        'name': compTag.attrib['name'],
                                        'maintainProportions': maintainProportions,
                                        'resizeToContainer' : resizeToContainer
                                        }
                return componentConfig
            else :
                return None
                
    def updateComponentConfig(self, componentName, componentType, configDict):
        if self.configFileLoaded == True:
            logging.debug("trying to find comp tag for component: %s", componentName)
            compTags = self.root.findall(".//*[@name='"+componentName+"']")
            
            if len(compTags) > 0:
                compTag = compTags[0]
                logging.debug ("found component, name: %s", compTag.attrib['name'])
                
                if componentType == 'ImagePanel':
                    compTag.attrib['texture'] = configDict['texture']
                    compTag.attrib['layer'] = str(configDict['layer'])
                    compTag.attrib['position'] = str(configDict['position'])
                    compTag.attrib['cliprect'] = str(configDict['cliprect'])
                    compTag.attrib['origin'] = str(configDict['origin'])
                    compTag.attrib['name'] = configDict['name']
                    
                    compTag.attrib['maintainProportions'] = str(configDict['maintainProportions'])
                    compTag.attrib['resizeToContainer'] = str(configDict['resizeToContainer'])
                
            else :
                return None
                
                
    def getComponentTransformations(self, componentName):
        transformationsList = []
        
        if self.configFileLoaded == True:
            logging.debug("trying to find comp tag for component: %s", componentName)
            compTags = self.root.findall(".//*[@name='"+componentName+"']")
            
            if len(compTags) > 0:
                compTag = compTags[0]
                logging.info ("found component, name: %s", compTag.attrib['name'])
                
                for transfTag in compTag:
                    if transfTag.tag == 'translation' and transfTag.attrib['enabled'] == 'True' :
                        transformationsList.append ( {
                                                    'transfType': transfTag.tag,
                                                    'enabled': transfTag.attrib['enabled'],
                                                    'XPdataref': transfTag.attrib['XPdataref'],
                                                    'indValueToTranslationTable': returnPointsList(transfTag.attrib['indValueToTranslationTable']),
                                                    'translationConvertFunction': transfTag.attrib['translationConvertFunction'],
                                                    'translationAngle': float(transfTag.attrib['translationAngle']),
                                                    'addAngleToRotation': float(transfTag.attrib['addAngleToRotation'])
                                                })
                    if transfTag.tag == 'rotation' and transfTag.attrib['enabled'] == 'True':
                        transformationsList.append ( {
                                                    'transfType': transfTag.tag,
                                                    'enabled': transfTag.attrib['enabled'],
                                                    'XPdataref': transfTag.attrib['XPdataref'],
                                                    'indValueToAnglesTable': returnPointsList(transfTag.attrib['indValueToAnglesTable']),
                                                    'rotationConvertFunction': transfTag.attrib['rotationConvertFunction']
                                                })
        logging.info("transformationsList : %s", transformationsList)
        return transformationsList
    
    def updatePanelConfig(self, position, size, name):
        if self.configFileLoaded == True:
            self.root.attrib['position'] = str(position)
            self.root.attrib['size'] = str([int(size[0]), int(size[1])])
            self.root.attrib['name'] = name
        
        
    def saveToFile(self):
        if self.configFileLoaded == True:
            self.tree.write(self.XMLconfigFilePath)
        else:
            logger.warning("No config file loaded, please create config file first")


class Panel(object):
    x = 0
    y = 0
    orig_x = 0
    orig_y = 0
    width = 0
    height = 0

    testMode = False
    testValue = 0

    visible = True
    name = ""
    
    def __init__(self,position, size, name = "Panel"):
        logging.info("init Panel %s", name)
        self.x = position[0]
        self.y = position[1]
        self.orig_x = position[0]
        self.orig_y = position[1]
        
        self.width = size[0]
        self.height = size[1]
        self.name = name

    def setVisible(self,visible):
        self.visible = visible
    
    def setPosition(self,coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.orig_x = coordinates[0]
        self.orig_y = coordinates[1]
    
    def setTestValue(self, testValue):
        self.testValue = testValue
        
    def setTestMode (self, testMode):
        self.testMode = testMode
    
    def getName(self):
        return self.name
        
    def getSize(self):
        return [self.width, self.height]
        
    def getPosition(self):
        return [self.x, self.y]
#--------------------------------------------------------------------------------------------------------------------
# class Container
# 
#--------------------------------------------------------------------------------------------------------------------
class Container(Panel):
    clipping = False
    
    previousMousePos = (0,0)
    
    previousMouseLeftBtnState = ""
    leftClicked = False
    
    previousMouseRightBtnState = ""
    rightClicked = False
    draggable = False
    dragged = False
    mousedisplacement_x = 0
    mousedisplacement_y = 0
    
    MOUSE_OVER_ME = False
    
    border = None
    selectedBorder = None
    visible = True
    
    backgroundRectangle = None
    backgroundRectangleSelected = None
    
    def __init__(self, XMLconfigFile = None, position =[0,0], size = [100,100], name = "Container"):
        logging.info("init Container %s, position: %s, size: %s, config file: %s", name, position, size, XMLconfigFile)
        Panel.__init__(self,position, size, name )
        self.itemList = []
        self.containerConfig = PanelFileConfig(XMLconfigFile)
        
    def initialise(self, batchImageRenderer = None): 
        self.setSelectedBorder(1, OpenGL3lib.COLOR_GREEN)
        self.batchImageRenderer = batchImageRenderer
        self.itemList = []
        
        contConfig = self.containerConfig.getPanelConfig()
                    
        self.setPosition(contConfig['position'])
        self.setSize(contConfig['size'])
        self.setName(contConfig['name'])
        
        contComponents = self.containerConfig.getComponents()
        
        for component in contComponents:
            if component['containerType'] == 'ImagePanel':
                imagePanel = ImagePanel (component['texture'], 
                                        self.batchImageRenderer, 
                                        component['layer'],
                                        component['position'],
                                        component['cliprect'],
                                        component['origin'],
                                        component['name'])
                
                
                compTransformations = self.containerConfig.getComponentTransformations(component['name'])
                
                for compTransformation in compTransformations:
                    if compTransformation['transfType'] == 'translation' :
                        imagePanel.enableTranslation(compTransformation['XPdataref'],
                                                    compTransformation['indValueToTranslationTable'],
                                                    conversionFunctions.conversionFunctionsDict[compTransformation['translationConvertFunction']],
                                                    compTransformation['translationAngle'],
                                                    compTransformation['addAngleToRotation'])
                    if compTransformation['transfType'] == 'rotation' :
                        imagePanel.enableRotation(compTransformation['XPdataref'],
                                                    compTransformation['indValueToAnglesTable'],
                                                    conversionFunctions.conversionFunctionsDict[compTransformation['rotationConvertFunction']])
                                                    

                self.addItem(imagePanel, component['position'], component['resizeToContainer'], component['maintainProportions'])
                
    def setBackgroundColor(self, color):
        self.backgroundRectangle = OpenGL3lib.GL_Filled_Rectangle(self.width, self.height, 1, color)
    
    def setBackgroundColorSelected(self, color):
        self.backgroundRectangleSelected = OpenGL3lib.GL_Filled_Rectangle(self.width, self.height, 1, color)
    
    def setName(self, name):
        self.name = name
    
    def getItemByName(self, itemName):
        for item in self.itemList:
            if item.name == itemName: 
                return item
        return None
        
    
    def addItem(self,item,relativePosition=[0,0], resize = True, maintainProportions = True):
        
        if resize == True:
            logging.info ("Container addItem, resizing item name %s, with width %s, height %s", item.name, item.width, item.height)
            
            if maintainProportions == True:
                itemlength = item.height
                if item.width > item.height:
                    itemlength = item.width
                length = self.height
                if self.width < self.height:
                    length = self.width
                    
                factor = length / itemlength
                item.resize([item.width*factor, item.height*factor])
            else:
                widthFactor =  self.width / item.width
                heightFactor = self.height / item.height 
                
                item.resize([item.width*widthFactor, item.height*heightFactor])
            
        if relativePosition == "CENTER":
            item_width = float(item.width)
            item_height = float(item.height)
            
            posx = self.x + float(self.width/2) - float(item_width/2)
            posy = self.y + float(self.height/2) - float(item_height/2)
            
            pos = [posx,posy]
        else: 
            pos = [self.x+relativePosition[0],self.y+relativePosition[1]]

            logging.debug("Container: %s, adding item: %s at position: %s of size %sx%s", self.name,item.getName(),pos, item.width, item.height)
        
        item.setPosition(pos)
        self.itemList.append(item)
    
    def setSize(self,size):
        self.width = size[0]
        self.height = size[1]
    
    def getSize(self):
        return [self.width, self.height]
    
    def resize(self,size, maintainContentProportions = True):
        logging.info("Resizing container to size:%s", size)
        if maintainContentProportions == True:
            for item in self.itemList:
                itemlength = item.height
                if item.width > item.height:
                    itemlength = item.width
                length = size[1]
                if size[0] < size[1]:
                    length = size[0]
                    
                factor = length / itemlength
                item.resize([item.width*factor, item.height*factor])
            
        else:
            widthFactor =  size[0] / self.width
            heightFactor = size[1] / self.height
            
            for item in self.itemList:
                item.resize([item.width*widthFactor, item.height*heightFactor])
        
        self.width = size[0]
        self.height = size[1]
            
  
    
    def setBorder(self,linewidth,color):
        self.border = OpenGL3lib.GL_rectangle(self.width,self.height,linewidth,color)
    
    def setSelectedBorder(self,linewidth,color):
        self.selectedBorder = OpenGL3lib.GL_rectangle(self.width,self.height,linewidth,color)
    
    def setPosition(self,coordinates):
        logging.info("Container set position, current [%s,%s] set to coordinates [%s,%s]", self.x, self.y, coordinates[0], coordinates[1])
        x_move = coordinates[0]-self.x
        y_move = coordinates[1]-self.y
        
        self.x += x_move
        self.y += y_move
        
        logging.info("Container new position [%s,%s]", self.x, self.y)
        for image in self.itemList:
            image_newpos = [image.x+x_move,image.y+y_move]
            image.setPosition(image_newpos)
    
    def moveBy(self,x_move,y_move):
        
        self.x += x_move
        self.y += y_move
        
        for item in self.itemList:
            item_newpos = (item.x+x_move,item.y+y_move)
            item.setPosition(item_newpos)
    
    def setVisible(self,visible):
        self.visible = visible
        for item in self.itemList:
            item.setVisible(visible)
            
    def draw(self):
        #logging.debug("drawing Container: %s, width: %s, height: %s", self.name, self.width, self.height)
        if self.visible == True:
            #if self.clipping == True:
                #logging.debug("glScissor(self.x: %s, self.y: %s, self.width: %s, self.height: %s)",self.x, self.y, self.width, self.height)
                #glScissor(self.x, self.y, self.width, self.height+1)
                #glEnable(GL_SCISSOR_TEST)
            
            for item in self.itemList:
                #logging.debug("drawing Container: %s, item: %s", self.name,item.getName())
                item.draw()
            if self.leftClicked == True:
                self.selectedBorder.draw(self.x,self.y)
            elif self.border != None:
                self.border.draw(self.x,self.y)
            
            if self.leftClicked == True and self.backgroundRectangleSelected != None:
                self.backgroundRectangleSelected.draw(self.x,self.y)
            elif self.backgroundRectangle != None:
                self.backgroundRectangle.draw(self.x,self.y)
            
            #if self.clipping == True:
                #logging.debug("end glScissor")
                #glDisable(GL_SCISSOR_TEST)
    
    def setClipping(self,clipping):
        self.clipping = clipping

    def setTestMode (self, testMode):
        self.testMode = testMode
        for item in self.itemList:
            item.setTestMode(testMode)
            
    def setTestValue(self, testValue):
        self.testValue = testValue
        for item in self.itemList:
            item.setTestValue(testValue)

    def mouseButtonCallback(self, button, action, mods):
        if self.MOUSE_OVER_ME == True and button == 0 and action == 1 :
            self.leftClicked = True
            self.previousMouseLeftBtnState = "DOWN"
        if self.MOUSE_OVER_ME == False and button == 0 and action == 1 :
            self.leftClicked = False
        
        if self.MOUSE_OVER_ME == True and button == 1 :
            self.rightClicked = True
            self.previousMouseRightBtnState = "DOWN"
        else:
            self.rightClicked = False
        
        if button == 0 and action == 0:
            self.previousMouseLeftBtnState = "UP"
            self.dragged = False
        if button == 1 and action == 0:
            self.previousMouseRightBtnState = "UP"
        
        #logging.debug("left clicked: %s, previous left button state: %s, action: %s  ", self.leftClicked, self.previousMouseLeftBtnState, action)
        
    def mouseCursorPosCallback(self, xpos, ypos):
        mousePos = OpenGL3lib.returnOpenGLcoord((xpos,ypos))
        
        if (mousePos[0] >= self.x) and (mousePos[0] <= (self.x+self.width)):
            if (mousePos[1] >= self.y) and (mousePos[1] <= (self.y+self.height)):
                self.MOUSE_OVER_ME = True
            else: 
                self.MOUSE_OVER_ME = False
        else:
            self.MOUSE_OVER_ME = False
            
        #print("mouse over me:", self.MOUSE_OVER_ME)
        self.dragged = False
        if (self.leftClicked == True) and (self.previousMouseLeftBtnState == "DOWN"): # I have been dragged
            self.dragged = True
            self.mousedisplacement_x = mousePos[0] - self.previousMousePos[0]
            self.mousedisplacement_y = mousePos[1] - self.previousMousePos[1]
            if self.draggable == True:
                self.moveBy(self.mousedisplacement_x,self.mousedisplacement_y)
        self.previousMousePos = mousePos
        
        #logging.debug("leftclicked:%s, dragged: %s, mouse move: %s, %s", self.leftClicked, self.dragged, self.mousedisplacement_x, self.mousedisplacement_y)
        
        
class Window(Container):
    MOUSE_OVER_TITLEBAR = False
    titleBarLeftClicked = False
    
    def __init__(self,position, size, pyGaugesPanel, GLFont, batchImageRenderer, layer = 0, name = "Window"):
        self.titleBarHeight = 25
        self.layer = layer
        logging.info("init Window %s, titleBarHeight: %s", name, self.titleBarHeight)
        Container.__init__(self,position, size, name )
        self.texture =    OpenGL3lib.GL_Texture("data/window/window_grey_transparent_bgd.png")

        self.setBorder(1,OpenGL3lib.COLOR_GREY)
        self.setSelectedBorder(1,OpenGL3lib.COLOR_WHITE)
        self.background = ImagePanel(self.texture, batchImageRenderer, self.layer, [0,0], [self.width,self.height],    [0    ,0    ])
        self.background.resize([self.width,self.height])
        self.addItem(self.background,(self.width/2,self.height/2),False)
        
        self.titleBarHeight = 25
        self.titleBarbackground = ImagePanel(self.texture, batchImageRenderer, self.layer, [0,0], [self.width,self.titleBarHeight],    [0    ,0    ])
        self.titleBarbackground.resize([self.width,self.titleBarHeight])
        
        self.titleBar = Container((0,0), (self.width,self.titleBarHeight),"Window title bar")
        self.titleBar.setBorder(1,OpenGL3lib.COLOR_GREY)
        self.titleBar.setSelectedBorder(1,OpenGL3lib.COLOR_WHITE)
        self.titleBar.addItem(self.titleBarbackground,(self.width/2,self.titleBarHeight/2),False)
        
        self.addItem(self.titleBar,(0,self.height-self.titleBarHeight),False)
        
        self.titleBarText = TextField(GLFont)
        self.titleBar.addItem(self.titleBarText, (5,(self.titleBarHeight/2-GLFont.textHeight/2)), False)
        
        pyGaugesPanel.registerMouseButtonCallback(self.mouseButtonCallback)
        pyGaugesPanel.registerMouseCursorPosCallback(self.mouseCursorPosCallback)

    def setTitleText(self, text):
        self.titleBarText.setText(text)

    def mouseButtonCallback(self, button, action, mods):
        if self.MOUSE_OVER_TITLEBAR == True and button == 0 and action == 1 :
            self.titleBarLeftClicked = True
            self.previousMouseLeftBtnState = "DOWN"
        if self.MOUSE_OVER_TITLEBAR == False and button == 0 and action == 1 :
            self.titleBarLeftClicked = False
        super(Window,self).mouseButtonCallback(button, action, mods)
        
    def mouseCursorPosCallback(self, xpos, ypos):
        
        mousePos = OpenGL3lib.returnOpenGLcoord((xpos,ypos))
        
        if (mousePos[0] >= self.x) and (mousePos[0] <= (self.x+self.width)):
            if (mousePos[1] >= self.y+self.height-self.titleBarHeight) and (mousePos[1] <= (self.y+self.height)):
                self.MOUSE_OVER_TITLEBAR = True
            else: 
                self.MOUSE_OVER_TITLEBAR = False
        else:
            self.MOUSE_OVER_TITLEBAR = False
            
        #print("mouse over me:", self.MOUSE_OVER_ME)
        self.dragged = False
        if (self.titleBarLeftClicked == True) and (self.previousMouseLeftBtnState == "DOWN"): # I have been dragged
            self.dragged = True
            self.mousedisplacement_x = mousePos[0] - self.previousMousePos[0]
            self.mousedisplacement_y = mousePos[1] - self.previousMousePos[1]
            self.moveBy(self.mousedisplacement_x,self.mousedisplacement_y)
        self.previousMousePos = mousePos
        
        #logging.debug("leftclicked:%s, dragged: %s, mouse move: %s, %s", self.leftClicked, self.dragged, self.mousedisplacement_x, self.mousedisplacement_y)
        super(Window,self).mouseCursorPosCallback(xpos, ypos)


class TextBox(Container):
    
    def __init__(self,position, size, eventManager, fontName, fontSize, fontColor, name = "TextBox"):
        logging.info("init TextBox %s ", name)
        Container.__init__(self,None, position, size, name )
        self.name = name
        
        self.setClipping(True)
        self.linespacing = 0
        
        self.buffer = collections.deque()
        self.textFieldsArray = []
        textField = OpenGL3lib.GL_Font(fontName, fontSize, fontColor, True, 0)
        self.nrDisplayedLines = (self.height // (textField.textHeight + self.linespacing))
        
        for i in range(0,self.nrDisplayedLines+1):
            textField = OpenGL3lib.GL_Font(fontName, fontSize, fontColor, True, 0)
            self.textFieldsArray.append([textField,(self.height -textField.textHeight -(textField.textHeight+self.linespacing)*i )])
        
    def writeLine(self,s):
        self.buffer.append(s)
        
    def draw(self):
        buffer = self.buffer
        bufferLength = len(self.buffer)
        if bufferLength <self.nrDisplayedLines:
            imin = 0
            imax = bufferLength
        else:
            imin = bufferLength - self.nrDisplayedLines
            imax = self.nrDisplayedLines+1
        for i in range (imin,bufferLength):
            self.textFieldsArray[i-imin][0].draw(buffer[i],self.x+2,self.y+self.textFieldsArray[i-imin][1])
        
        #super(TextBox,self).draw()
        
class InputTextField(Container):
    
    
    def __init__(self,position, size, pyGaugesPanel, fontName, fontSize, fontColor, name = "InputTextField"):
        logging.info("init InputTextField %s ", name)
        Container.__init__(self,None,position, size, name )
        self.entryAccepted = False
        self.setBorder(1,OpenGL3lib.COLOR_GREY)
        self.setSelectedBorder(1,OpenGL3lib.COLOR_WHITE)
        self.setBackgroundColor(OpenGL3lib.COLOR_BLACK)
        self.setBackgroundColorSelected(OpenGL3lib.COLOR_BLUE)
        self.textField = OpenGL3lib.GL_Font(fontName, fontSize, fontColor, True, 0)
        self.textHintField = OpenGL3lib.GL_Font(fontName, fonts.FONT_SIZE_MED, fontColor, True, 0)
        
        self.hintList = None
        self.possibleHints = []
        self.hintListBackground = None
        
        self.text = ""
        
        self.name = name
        pyGaugesPanel.registerMouseButtonCallback(self.mouseButtonCallback)
        pyGaugesPanel.registerMouseCursorPosCallback(self.mouseCursorPosCallback)
        pyGaugesPanel.registerKeyCallback(self.keyCallback)
        pyGaugesPanel.registerCharCallback(self.charCallback)
        
    def addHintList(self,hintList):
        self.hintList = hintList
        self.hintListBackground = OpenGL3lib.GL_Filled_Rectangle(self.width, 20, 1, OpenGL3lib.COLOR_BLUE)
    
    def charCallback(self,codepoint):
        print(codepoint)
        if (codepoint >= 32 and codepoint <= 126) or (codepoint >= 256 and codepoint <= 270) :    # only print printable characters
            self.text += unichr(codepoint)
        
    def keyCallback(self,key, scancode, action, mods):
        
        if self.leftClicked == True:
            self.haveFocus = True
        
        if action == glfw.GLFW_PRESS and self.leftClicked == True:
            #print ("key id:", key, "KEY UNICODE: ", event.unicode)
            #if (event.key >= 32 and event.key <= 126) or (event.key >= 256 and event.key <= 270) :    # only print printable characters
            #    self.text += event.unicode
            
            if key == glfw.GLFW_KEY_BACKSPACE:
                self.text = self.text[:-1]
            if key == glfw.GLFW_KEY_DELETE:
                self.text = ""
            
            self.possibleHints = [k for k in self.hintList if self.text in k]
            print ('possible Hints', self.possibleHints)
            
            if (key == glfw.GLFW_KEY_ENTER or key == glfw.GLFW_KEY_KP_ENTER) and len(self.possibleHints)>0 :
                self.text = self.possibleHints[0]
                self.entryAccepted = True
            else:
                self.entryAccepted = False
            
    def draw(self):
        super(InputTextField,self).draw()
        self.textField.draw(self.text,self.x+2,self.y+2)
        if self.hintList !=None and len(self.possibleHints)>0 and self.leftClicked == True and self.text !="":
            self.hintListBackground.draw(self.x,self.y+21)
            self.textHintField.draw("Hint [Enter to accept]: "+self.possibleHints[0],self.x+2,self.y+22) 
        

class ImagePanel(Panel):
    image = None

    addTranslation = (0,0)
    
    valueToRotAnglesTable= [ [0,0]]
    valueToMoveTable = [ [0,0]]
    
    rotating = False
    translating = False
    translationAngle = None
    
    rotationXPdata = False
    rotationCenter = None
    textureRotationCenter = None
    
    translationXPdata = False
    
    rotationConvertFunction = False
    translationConvertFunction = False
    
    visibilityXPData = None
    visibilityToggleFunction = None
    
    refreshVisibility = True
    refreshPosition = True
    refreshRotation = False
    refreshTextTranslation = False
    refreshTextRotation = False
    refreshTextZoom = True
    refreshSize = True
    
    textTranslating = False
    textTranslationConvertFunction = None
    textTranslationXPdata = None
    textValueToMoveTable = None
    
    textRotating = False
    textRotationConvertFunction = None
    textRotationXPdata = None
    textValueToRotationTable = None
    
    testRotationValue = 0
    testTranslationValue = 0
    
    addRotAngleForTranslation = 0
    rot_angle = 0.0
    previous_rot_angle = 0.0
    
    text_rot_angle = math.radians(0.0)
    previous_text_rot_angle = 0.0
    
    xdev = 0.0
    ydev = 0.0
    previous_xdev = 0.0
    previous_ydev = 0.0

    text_xdev = 0.0
    text_ydev = 0.0
    previous_text_xdev = 0.0
    previous_text_ydev = 0.0
    text_zoom = 1.0
    previous_text_zoom = 1.0
    
    
    def __init__(self, texturePath, batchImageRenderer, layer=0, position=[0,0], cliprect=None, origin=None, name = ""):
        logging.info("Initialise ImagePanel name:%s texture:%s layer:%s position:%s cliprect:%s origin:%s", name, texturePath, layer, position, cliprect, origin)
        self.batchImageRenderer = batchImageRenderer
        glTexture = OpenGL3lib.GL_Texture(texturePath)
        self.image = OpenGL3lib.GL_Image(glTexture,cliprect,origin)
        Panel.__init__(self,position, (self.image.width,self.image.height), glTexture.name)
        self.name = name
        batchImageRenderer.addImageToRenderQueue(self.image,layer)
        self.image.draw((self.x,self.y),self.width,self.height,None,self.rot_angle, self.rotationCenter, (self.text_xdev, self.text_ydev),self.text_rot_angle,self.text_zoom)
        
    def setPosition(self,coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.orig_x = coordinates[0]
        self.orig_y = coordinates[1]
        #self.image.draw((self.x,self.y),self.width,self.height,None,self.rot_angle, self.rotationCenter, (self.text_xdev, self.text_ydev),self.text_rot_angle,self.text_zoom)
        self.refreshPosition = True
        #self.image.needRefresh = True
    
    def setVisible(self,visible):
        if self.visible != visible:
            logging.debug("Visibility changed: "+str(visible))
            self.refreshVisibility = True
            self.visible = visible
            self.image.visible = visible
    
    def translateTexture(self, textXdev, textYdev):
        self.text_xdev = textXdev
        self.text_ydev = textYdev
        self.refreshTextTranslation = True
        
    def rotateTexture(self,angle):
        self.text_rot_angle = math.radians(angle)
        self.refreshTextRotation = True
    
    ## rotate the Image panel by provided angle in degrees - note the function will rotate the Image to the angle provided.
    # @param angle - angle to rotate in degrees. Call ImagePanel.rotateToAngle(90) if you want to rotate to 90 degrees for example
    #
    def rotateToAngle(self,angle):
        self.previous_rot_angle = self.rot_angle
        self.rot_angle = math.radians(angle)
        
        self.refreshRotation = True
        
    def zoomTexture(self, textZoom):
        self.text_zoom = textZoom
        self.refreshTextZoom = True
    
    def enableTextureTranslation(self,dataSourceReference, indValueToTranslationTable, translationConvertFunction = False):
        self.textTranslating = True
        self.textTranslationConvertFunction = translationConvertFunction
        
        self.textTranslationXPdata = dataSourceReference
        self.textValueToMoveTable = self.createFactorsTable(indValueToTranslationTable)
    
    def enableTextureRotation(self,dataSourceReference, indValueToRotationTable, rotationConvertFunction = False):
        self.textRotating = True
        self.textRotationConvertFunction = rotationConvertFunction
        
        self.textRotationXPdata = dataSourceReference
        self.textValueToRotationTable = self.createFactorsTable(indValueToRotationTable)
    
    def setAddTranslation(self, translation):
        self.addTranslation = translation

    def resize(self,size):
        if self.image != None:
            logging.info("ImagePanel name: %s resizing to size %s", self.name, size)
            
            self.width = size[0]
            self.height = size[1]
            self.image.resize(self.width,self.height)
            
            self.refreshSize = True
            #self.image.needRefresh = True

    def toggleVisibility(self, dataSourceReference, visibilityToggleFunction = False):
        self.visibilityToggleFunction = visibilityToggleFunction
        self.visibilityXPData = dataSourceReference
        
    def enableRotation(self, dataSourceReference, indValueToAnglesTable, rotationConvertFunction = False):
        self.rotating = True
        self.rotationConvertFunction = rotationConvertFunction
        self.rotationXPdata = dataSourceReference
        self.valueToRotAnglesTable = self.createFactorsTable(indValueToAnglesTable)

    def setRotationCenter(self,rotationCenter):
        self.rotationCenter = rotationCenter
    
    def setTextureRotationCenter(self,rotationCenter):
        self.textureRotationCenter = rotationCenter
    
    def enableTranslation(self,dataSourceReference, indValueToTranslationTable, translationConvertFunction = False,translationAngle=None,addAngleToRotation=None):
        self.translating = True
        self.translationConvertFunction = translationConvertFunction
        if translationAngle:
            self.translationAngle = translationAngle
        if addAngleToRotation:
            self.addRotAngleForTranslation = addAngleToRotation
        self.translationXPdata = dataSourceReference
        self.valueToMoveTable = self.createFactorsTable(indValueToTranslationTable)
        
    def draw(self):
        #logging.debug("update "+str(self.name))
        #def draw(self, abspos=None, relpos=None, width=None, height=None,
        #color=None, rotation=None, rotationCenter=None):
        
        needRefresh = False #SHOULD BE FALSE
        self.image.needRefresh = False
        
        if self.visibilityXPData:
            
            if self.testMode == False:
                XPindicatedValue = float(XPUDP.pyXPUDPServer.getData(self.visibilityXPData))
            else: 
                XPindicatedValue = self.testValue
                
            self.image.visible = self.visibilityToggleFunction(XPindicatedValue)
            self.visible = self.image.visible
            logging.debug("VisibilityXPdata: %s", self.image.visible)
            needRefresh = True
            
        if self.refreshVisibility == True:
            logging.debug("draw: Visibility needs to be changed"+str(self.visible))
            self.refreshVisibility = False 
            self.image.visible = self.visible
            needRefresh = True
        
        if self.rotating == True:
            if self.testMode == False:
                XPindicatedValue = XPUDP.pyXPUDPServer.getData(self.rotationXPdata)
                logging.debug(self.rotationXPdata)
                logging.debug("XP Rotation value:%s", XPindicatedValue)
            else: 
                XPindicatedValue = self.testValue
            
            if self.rotationConvertFunction != False :
                XPindicatedValue = float(self.rotationConvertFunction(XPindicatedValue))
            
            #print("XP Rotation value:", XPindicatedValue)
            self.rot_angle = math.radians(self.convertValueToTransformValue(XPindicatedValue,self.valueToRotAnglesTable))
            
            if abs(self.rot_angle-self.previous_rot_angle) > math.radians(0.1) :
                needRefresh = True
                self.previous_rot_angle = self.rot_angle
        
        if self.refreshRotation == True:
            needRefresh = True
            self.previous_rot_angle = self.rot_angle
        
        if self.translating == True:
            if self.testMode == False:
                XPindicatedValue = float(self.XPUDPServer.getData(self.translationXPdata))
            else: 
                XPindicatedValue = self.testValue
            
            if self.translationConvertFunction != False :
                XPindicatedValue = float(self.translationConvertFunction(XPindicatedValue))
            
            translationAmount = self.convertValueToTransformValue(XPindicatedValue,self.valueToMoveTable)
            #print self.image_name," XP indicated value: ",XPindicatedValue, " transl amount = ", translationAmount
            
            if self.translationAngle: 
                transl_angle_rad = math.radians(self.translationAngle)
            else:
                transl_angle_rad = self.rot_angle + math.radians(self.addRotAngleForTranslation)
            
            self.xdev = translationAmount * math.sin(transl_angle_rad) + self.addTranslation[0]
            self.ydev = translationAmount * math.cos(transl_angle_rad) + self.addTranslation[1]
            if abs(self.xdev-self.previous_xdev) > 0.1 :
                needRefresh = True
                self.previous_xdev = self.xdev
            if abs(self.ydev-self.previous_ydev) > 0.1 :
                needRefresh = True
                self.previous_ydev = self.ydev
        
        if self.textRotating == True:
            if self.testMode == False:
                XPindicatedValue = float(XPUDP.pyXPUDPServer.getData(self.textRotationXPdata))
            else: 
                XPindicatedValue = self.testValue
            
            if self.textRotationConvertFunction != False :
                XPindicatedValue = float(self.textRotationConvertFunction(XPindicatedValue))
            #logging.debug("text rotation, XP value = %s", XPindicatedValue)
            self.text_rot_angle = math.radians(self.convertValueToTransformValue(XPindicatedValue,self.textValueToRotationTable))
            #logging.debug("text rotation, XP value = %s, rot angle rad = %s", XPindicatedValue, self.text_rot_angle)
        
        if self.textTranslating == True:
            if self.testMode == False:
                XPindicatedValue = float(XPUDP.pyXPUDPServer.getData(self.textTranslationXPdata))
            else: 
                XPindicatedValue = self.testValue
            
            if self.textTranslationConvertFunction != False :
                XPindicatedValue = float(self.textTranslationConvertFunction(XPindicatedValue))
            
            translationAmount = self.convertValueToTransformValue(XPindicatedValue,self.textValueToMoveTable)
            #print ("Texture translation", self.name," XP indicated value: ",XPindicatedValue, " text transl amount = ", translationAmount)
            
            transl_angle_rad = self.text_rot_angle #+ math.radians(self.addRotAngleForTranslation)
            
            self.text_xdev = 0.0#-translationAmount #* math.sin(transl_angle_rad) 
            self.text_ydev = -translationAmount #* math.cos(transl_angle_rad) 
            #print ("after mult by rot, text xdev, ydev = ",self.text_xdev, self.text_ydev)
        
        if self.refreshPosition == True:
            logging.debug("Imagepanel refresh position")
            needRefresh = True
            self.refreshPosition = False
        
        if self.refreshSize == True:
            logging.info("Imagepanel refresh size, ImagePanel size =%s, %s", self.width, self.height)
            needRefresh = True
            self.image.resize(self.width,self.height)
            self.batchImageRenderer.fillBuffers()
            self.refreshSize = False
        
        if self.textTranslating == True or self.refreshTextTranslation == True:
            #print "self.refreshTextTranslation = ", self.refreshTextTranslation
            #if abs(self.text_xdev-self.previous_text_xdev) > 0.1 :
            needRefresh = True
            self.previous_text_xdev = self.text_xdev
            #print ("I need refresh on text x")
            #if abs(self.text_ydev-self.previous_text_ydev) > 0.1 :
            #needRefresh = True
            self.previous_text_ydev = self.text_ydev
            #print ("I need refresh on text y")
            self.refreshTextTranslation = False
        
        if self.textRotating == True or self.refreshTextRotation == True:
            #print ("refresh text rotation")    
            if abs(self.text_rot_angle-self.previous_text_rot_angle) > math.radians(0.1) :
                needRefresh = True
                self.previous_text_rot_angle = self.text_rot_angle
            self.refreshTextRotation = False
            
        if self.refreshTextZoom == True:
            if abs(self.text_zoom-self.previous_text_zoom) > 0.01 :
                needRefresh = True
                self.previous_text_zoom = self.text_zoom
            self.refreshTextZoom = False
        
        #logging.debug("drawing image %s, at x: %s, y %s, width: %s, height: %s ", self.name, self.x, self.y,self.width, self.height ) #print "x: ", self.x, "y: ", self.y
        #if self.testMode == True:
            #print "drawing ", self.name
        if needRefresh == True:
            logging.info("I need to be refreshed")
            self.image.needRefresh = True
            self.image.draw((self.x+self.xdev,self.y+self.ydev),
                            self.width,self.height,None,
                            self.rot_angle, self.rotationCenter, 
                            (self.text_xdev, self.text_ydev),
                            self.text_rot_angle,self.text_zoom, 
                            self.textureRotationCenter)
            #needRefresh = False

    # calculate the transformation value (angle or translation)- using the translation table - returns a linear calculation between 2 values in the table
    def convertValueToTransformValue(self,indicatedValue, translationTable):
        '''
        [     [0,-124.5],                [0,        -124.5,        a,     b ]
            [500,-94],                [500,     -94,        a,     b ]
            [1000,-64.5],
            [1800,0],
            [2000,15.5],
            [2200,32],
            [2500,55],
            [2600,62],
            [2700,70.5],
            [3500,125.5]]
        '''
        
        if indicatedValue <=translationTable[0][0]:
            return translationTable[0][1]
        length = len(translationTable)
        for i in range(0,length):
            if i == length-1:
                transformValue = translationTable[length-1][1]
                return transformValue
            elif translationTable[i][0] <= indicatedValue and translationTable[i+1][0]>=indicatedValue:
                transformValue = translationTable[i][2]*indicatedValue + translationTable[i][3]
                return transformValue
    
    def createFactorsTable (self, translationTable):
        factorsTable = []

        for i in range(0,len(translationTable)-1):
            a = float(    float(translationTable[i][1]-translationTable[i+1][1])
                       /float(translationTable[i][0]-translationTable[i+1][0]))
            b = float(    float(translationTable[i][0]*translationTable[i+1][1] - translationTable[i][1]*translationTable[i+1][0])
                       /float(translationTable[i][0]-translationTable[i+1][0]))
            
            factorsTable.append([float(translationTable[i][0]), float(translationTable[i][1]), a, b])
        factorsTable.append([float(translationTable[len(translationTable)-1][0]), float(translationTable[len(translationTable)-1][1]), 1, 0])
        
        logging.debug("createFactorsTable  :: translation table: %s", translationTable)
        logging.debug("createFactorsTable  :: factorsTable table: %s", factorsTable)
        
        return factorsTable
        

class TextField(Container):
    
    def __init__(self, font):
        self.image = font
        self.text = ""
        self.XPUDPServer = None
        self.textDataSourceReference = None
        self.textFormat = '{:.1f}'
        self.unitText = ""
        self.prefixUnit = False
        self.dataConvertFunction = False
        
        Container.__init__(self,None,(0,0), (650,25))
        
    ## Sets the text to be displayed (static value). Note this will have no effect if you have set the TextField instance to display an XPlane value with the setTextDataSource method. 
    # If you want to temporarily display a static text rather than the XPlane value, call setTextDataSource(None) first. You will need to call setTextDataSource() again to re enable the XPlane UDP value if required later on.
    # @param s: The text string to be displayed
    #
    def setText(self, s):
        self.text = s
    
    def setVisible(self,visible):
        self.visible = visible
        self.image.visible = visible
    
    def setPosition(self,coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.orig_x = coordinates[0]
        self.orig_y = coordinates[1]
        self.image.draw((self.x,self.y),self.width,self.height)
        
        self.refreshPosition = True
        self.image.needRefresh = True
        
    def setTextDataSource(self, textDataSourceReference, dataConvertFunction = False):
        self.XPUDPServer = XPlaneUDPServer.pyXPUDPServer
        
        self.textDataSourceReference = textDataSourceReference
        self.dataConvertFunction = dataConvertFunction
    
    def setDisplayUnit(self, unitText, prefix = False ):
        self.unitText = unitText
        self.prefixUnit = prefix
    
    def setTextFormat(self, textFormat):
        self.textFormat = textFormat
    
    def draw(self):
        if self.visible == True:
            super(TextField,self).draw()
            XPValue = 0
            if self.XPUDPServer != None and self.textDataSourceReference != None:
                XPValue = self.XPUDPServer.getData(self.textDataSourceReference)
                if self.dataConvertFunction != False:
                    XPValue = float(self.dataConvertFunction(XPValue,self.XPUDPServer))
                
                self.text =  self.textFormat.format(float(XPValue))
                self.text += self.unitText

            #logging.debug("drawing text %s, at x: %s, y %s ", self.text, self.x, self.y )
            self.image.draw(self.text,self.x,self.y)
            
            



class AnimatedImage(ImagePanel):
    def __init__(self, imageDir, imageBaseName, startStepNumber, endStepNumber, imageNameSuffix, indexPadding,  position=[0,0], cliprect=None, origin=None, testMode=False):
        self.image_name = imageBaseName
        logging.info("init AnimatedImage %s", self.image_name)
        imageBaseName = os.path.join(imageDir, imageBaseName)
        self.startStepNumber = startStepNumber
        self.endStepNumber = endStepNumber
        self.visibleFrame = startStepNumber
        
        self.imageFrames = {}
        
        if endStepNumber >= startStepNumber :
            for i in range(startStepNumber,endStepNumber+1) :
                index = str(i).zfill(indexPadding)
                
                imagename = imageBaseName + index + imageNameSuffix
                logging.debug("loading AnimatedImage %s", imagename)
                self.imageFrames[i] = OpenGL3lib.GL_Image(imagename,cliprect,origin)

        self.x = position[0]
        self.y = position[1]
        self.width = self.imageFrames[startStepNumber].width
        self.height = self.imageFrames[startStepNumber].height
        
        self.testMode = testMode
        self.testValue = 1
        self.dataConvertFunction = False
        self.XPdataSource = False
        self.dataSourceReference = False
        
    def resize(self,size):
        for i in range(self.startStepNumber,self.endStepNumber+1) :
            self.imageFrames[i].resize(size[0],size[1])
        self.width = self.imageFrames[self.startStepNumber].width
        self.height = self.imageFrames[self.startStepNumber].height
    
    def setAnimationDataValue(self,XPdataSource, dataSourceReference, dataConvertFunction = False):
        self.dataConvertFunction = dataConvertFunction
        self.XPdataSource = XPdataSource
        self.dataSourceReference = dataSourceReference
    
    def draw(self):
        if self.testMode == True :
            drawIndex = int(self.testValue%360)
        else :
            drawIndex = int(self.XPdataSource.getData(self.dataSourceReference))
        if self.dataConvertFunction != False:
            drawIndex = self.dataConvertFunction(drawIndex,self.XPdataSource)
        
        self.imageFrames[drawIndex].draw((self.x,self.y),(0,0),self.width,self.height)
    
    
