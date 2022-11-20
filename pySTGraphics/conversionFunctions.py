import math
import decimal
D = decimal.Decimal
import pyxpudpserver as XPUDP


## Convert input elapsed time in seconds to hh:mm equivalent, and return the mm minutes 
# @param inValue float elapsed time in seconds 
#
def returnMinutes(inValue):
    outValue = inValue//60.0 #total minutes elapsed
    outValue = outValue%60.0
    
    return outValue

## Convert input elapsed time in seconds to hh:mm equivalent, and return the hh minutes 
# @param inValue float elapsed time in seconds 
#
def returnHours(inValue):
    outValue = inValue/60.0 #total minutes elapsed
    outValue = outValue//60.0 #total hours elapsed
    
    return outValue

## Given an altitude in feet, return the corresponding altitude in 100s feet 
# @param inValue float altitude in feet 
#
def returnAltitude100sfeet(inValue):
    outValue = inValue//100.0 
    return outValue


def modulo360(inValue):
    outValue = inValue%360
    return outValue

def divideby100(inValue):
    outValue = float(inValue)/100.0
    return outValue

def returnSpeedLabelValue(inValue):
    outValue = int(float(inValue+0.5)/10.0)
    return outValue

def returnSpeedTapeValue(inValue):
    outValue = int(inValue)
    outValue = float(outValue)/10
    outValue = outValue%1*10
    outValue = float(outValue)+float(inValue%1)
    return outValue
    
def returnSpeed100sValue(inValue):
    # 215.27
    outValue = int(inValue)
    #215
    outValue = float(outValue)/100
    #2.15
    outValue = outValue%1*100
    #15
    outValue = float(outValue)+float(inValue%1)
    return outValue

def roundToNearest10(inValue):
    #8980
    outValue = (D(inValue)//D(10))*10
    return outValue


def returnAlti100sDigit(inValue):
    #8980
    outValue = (D(inValue)/D(1000))%1
    #8.980%1 = 0.980
    outValue = D(outValue)*10
    #9.80
    return D(outValue)//D(1)

def returnAlti10s(inValue):
    # 14215.27
    outValue = float(inValue)/100
    #142.1527
    outValue = outValue%1*100
    return outValue
    
def returnAlti1k10kDigits(inValue):
    # 15215.27
    outValue = int(inValue/1000)
    #15.21527
    return outValue
    
def convertINtomb(inValue):
    outValue = inValue*33.863753
    #print "inValue: ", inValue, "outValue: ", outValue
    return outValue

def convertSuction(inValue):
    outValue = inValue*2.8
    #print "inValue: ", inValue, "outValue: ", outValue
    return outValue

def convertLbsToGallons(XPindicatedValue):
    XPindicatedValue = XPindicatedValue/6
    return XPindicatedValue
    
def return100s(XPindicatedValue):
    XPindicatedValue = XPindicatedValue/1000
    XPindicatedValue = XPindicatedValue%1
    return XPindicatedValue

def return1000s(XPindicatedValue):
    XPindicatedValue = XPindicatedValue/10000
    XPindicatedValue = XPindicatedValue%1
    return XPindicatedValue

def return10000s(XPindicatedValue):
    XPindicatedValue = XPindicatedValue/100000
    XPindicatedValue = XPindicatedValue%1
    return XPindicatedValue

def addCompassHeadingToValue(XPindicatedValue):
    bugHeading = XPindicatedValue - XPUDP.pyXPUDPServer.getData("sim/cockpit2/gauges/indicators/heading_vacuum_deg_mag_pilot[0]")
    if bugHeading < 0:
        bugHeading = bugHeading+360
    return bugHeading
    
def addNondriftCompassHeadingToValue(XPindicatedValue):
    bugHeading = XPindicatedValue - XPUDP.pyXPUDPServer.getData((17,3))
    if bugHeading < 0:
        bugHeading = bugHeading+360
    return bugHeading

def calculateTurnRate(XPindicatedValue):
    roll = math.radians(XPUDP.pyXPUDPServer.dataList[17][1])
    pitch = math.radians(XPUDP.pyXPUDPServer.dataList[17][0])
    Q = XPUDP.pyXPUDPServer.dataList[16][0]
    P = XPUDP.pyXPUDPServer.dataList[16][1]
    R = XPUDP.pyXPUDPServer.dataList[16][2]
    
    turnRate = Q * math.sin(roll)/math.cos(pitch) + R * math.cos(roll)/math.cos(pitch)
    turnRate = turnRate * 180/math.pi
    #print "Turn rate: ", turnRate
    return turnRate

def NAV_TO_Toggle(XPindicatedValue):
    val = int(XPindicatedValue)
    if val == 1:
        return True
    else:
        return False

def NAV_FR_Toggle(XPindicatedValue):
    val = int(XPindicatedValue)
    if val == 2:
        return True
    else:
        return False
        
def NAV_FLG_Toggle (XPindicatedValue):
    val = int(XPindicatedValue)
    if val == 0:
        return True
    else:
        return False

def NAV_GSFLG_Toggle (XPindicatedValue):
    val = int(XPindicatedValue)
    if val != 10:
        return True
    else:
        return False

## returns True if the value passed is greater than 0, False otherwise 
# @param inValue float value 
#
def returnTrueIfOverZero(XPindicatedValue):
    if XPindicatedValue > 0.0:
        return True
    else:
        return False
        

conversionFunctionsDict = {
    'returnMinutes' : returnMinutes,
    'returnHours' : returnHours,
    'returnAltitude100sfeet' : returnAltitude100sfeet,
    'modulo360' : modulo360,
    'divideby100' : divideby100,
    'returnSpeedLabelValue' : returnSpeedLabelValue,
    'returnSpeedTapeValue' : returnSpeedTapeValue,
    'returnSpeed100sValue' : returnSpeed100sValue,
    'roundToNearest10' : roundToNearest10,
    'returnAlti100sDigit' : returnAlti100sDigit,
    'returnAlti10s' : returnAlti10s,
    'returnAlti1k10kDigits' : returnAlti1k10kDigits,
    'convertINtomb' : convertINtomb,
    'convertSuction' : convertSuction,
    'convertLbsToGallons' : convertLbsToGallons,
    'return100s' : return100s,
    'return1000s' : return1000s,
    'return10000s' : return10000s,
    'addCompassHeadingToValue' : addCompassHeadingToValue,
    'addNondriftCompassHeadingToValue' : addNondriftCompassHeadingToValue,
    'calculateTurnRate' : calculateTurnRate,
    'NAV_TO_Toggle' : NAV_TO_Toggle,
    'NAV_FR_Toggle' : NAV_FR_Toggle,
    'NAV_FLG_Toggle' : NAV_FLG_Toggle,
    'NAV_GSFLG_Toggle' : NAV_GSFLG_Toggle,
    'returnTrueIfOverZero' : returnTrueIfOverZero
}
