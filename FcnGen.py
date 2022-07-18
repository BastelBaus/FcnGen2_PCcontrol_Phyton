# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 19:03:51 2022

@author: pagan
"""

import serial.tools.list_ports
import serial
import socket
import time   # for sleep


from Utils import tic,toc 


from FcnGenInterfaceETH import FcnGenInterfaceETH
from FcnGenInterfaceCOM import FcnGenInterfaceCOM
import FcnGenInterface as FGIF
import Command as Cmd


import my_logger
logger = my_logger.get_logger(__name__)   


        
    
            
class FcnGen:

    def __init__(self,IP=None, port=None,baudrate=115200):
        self.IP = IP;
        self.port=port
        self.baudrate=baudrate

    def __del__(self):
       logger.error("del FcnGen")
       self.disconnect()

    def close(self):
       logger.error("Close FcnGen")
       self.disconnect()
        
    def disconnect(self):
       logger.error("Disconnect FcnGen")
       if hasattr(self,"s"): # and self.s is not None: 
            self.s.disconnect(); 
            logger.error(f"FcnGen del self.s")
            self.s.release(); 
            logger.error(f"FcnGen del self.s")
            del self.s
            logger.error(f"deleted super")
        
    def connect(self,IP=None, port=None,baudrate=115200):
        logger.debug(f"Connection to IP:{IP}, port:{port}, baudrate:{baudrate}")
        #if hasattr(self,"s") and self.s is not None: 
        if hasattr(self,"s"): self.s.disconnect(); del self.s 
        if IP is None: IP = self.IP
        if port is None: port = self.port
        if IP is not None:
            self.s = FcnGenInterfaceETH(IP,port)
        elif port is not None:
            self.s = FcnGenInterfaceCOM(port,baudrate)
        else: 
            logger.warning("Trying to connect but no valid address given IP:%s, Port:%s"%(str(IP),str(port)))
            return False
        return self.s.connect()

    def getListOfCOMPorts(self): return [a.device for a in serial.tools.list_ports.comports()]        
    def getListOfCOMBaudrates(self): return list(serial.Serial.BAUDRATES)
    
    def hasConObj(self):
        """ returns true if the con object s can be accessed """
        return hasattr(self,"s") and self.s is not None

    def isConnected(self):
        if self.hasConObj(): return self.s.isConnected()
        return False
        
    
    # if CMD, call for every function, else only if mathcing
    def add_subscription(self,call,cmd=None,consumer=False):
        if self.hasConObj():  self.s.add_subscription(call,cmd,consumer)
        else: logger.warning("tried to subscribe to interface wich is not connected")
    


    def queryCommand(self,cmd):  
        if self.isConnected():  return self.s.queryln( Cmd.Request(cmd) )
        else:                   return None

    
    # Channel: 1,2 or 3 for both
    def setConfig(self,config,channel=1):  
        if self.hasConObj(): self.s.write( b"s%d\n" % config )
    def setGain(self,gain,channel=1):      
        if self.hasConObj(): self.s.write( b"g%d\n" % gain )


    def genericRequest(self,cmd):
        if not self.hasConObj(): return None   
        cmd = Cmd.Request( cmd )  
        responce = self.s.queryln( cmd )
        if responce.isOK(): return responce
        logger.warning("Received non valid responce: " + str(responce).rstrip() + " to command:" + str(cmd))
        return None

    def genericCommand(self,cmd):  
        if not self.hasConObj(): return None   
        return self.genericRequest ( Cmd.Request(cmd) ) 
    
    def getChannelConfig(self,channel=0):  
        if not self.hasConObj(): return None   
        responce = self.genericRequest ( Cmd.Request( f"!L:{channel}" ) ) 
        return [] if responce is None else responce.getParams().split(",")        

    def getParameter(self,parID):
        if not self.hasConObj(): return None   
        responce = self.genericRequest ( Cmd.Request( f"$:{parID}" ) ) 
        return [] if responce is None else responce.getParams().split(":")

    def writeParameter(self,parID,value):
        if not self.hasConObj(): return None   
        responce = self.genericRequest ( Cmd.Request( f"%:{parID}:{value}" ) ) 
        return True
        
    def checkAlive(self):  
        if not self.hasConObj(): return None   
        responce = self.genericRequest ( Cmd.Request( f"!A" ) ) 
        #print("RESPONCE----------------------------->",str(responce))
        return True

    def checkDebug(self):  
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f"!D" ) ) 
        return True

    def getAmplitudeRange(self,channel=1):  
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:q:minA,maxA\n" ) ) 
        return [] if responce is None else responce.getParams().split(":")

    def getOffsetRange(self,channel=1):  
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:q:minO,maxO\n" ) ) 
        return [] if responce is None else responce.getParams().split(":")


    def getLimits(self,channel=1): # note limits are mode dependent   
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:q:minF,maxF,minA,maxA,minO,maxO\n" ) ) 
        return [] if responce is None else responce.getParams().split(":")
    
    
    def getUnhandledResponces(self): 
        if self.s: return [ str(c) for c in self.s.getUnhandledResponces() ]
        else: return None
    

    def setFrequency(self,frequency,channel=1): 
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:F:{frequency}" ) ) 
        return None if responce is None else responce.getParams().split(":")
    def setAmplitude(self,amplitude,channel=1,mode=0):      
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:A:{amplitude}" ) ) 
        return None if responce is None else responce.getParams().split(":")
    def setOffset(self,offset,channel=1):     
        if not self.s: return None             
        responce = self.genericRequest ( Cmd.Request( f">{channel}:O:{offset}" ) ) 
        return None if responce is None else responce.getParams().split(":")
    
    

    def setSinus(self,channel=1):          
        #if self.s: self.s.write( b"ts\n" )
        if self.s: self.s.write( (f">{channel}:m:sin\n").encode() )
    def setTriangle(self,channel=1):       
        #if self.s: self.s.write( b"tt\n" )
        if self.s: self.s.write( (f">{channel}:m:triangle\n").encode() )
    def setSquare(self,channel=1):    
        #if self.s: self.s.write( b"tQ\n" )
        if self.s: self.s.write( (f">{channel}:m:square\n").encode() )

    def setHalfSquare(self,channel=1):     
        if self.s: self.s.write( b"tH\n" )

    def doReboot(self):                    
        if not self.s: return False
        responce = self.genericRequest ( Cmd.Request( "!x" ) ) 
        return True
     
        
     
        
     
    #def setParameter(self,param,value,channel=0):      
    #    if   param == "frequency": self.setFrequency(value,channel)
    #    elif param == "amplitude": self.setAmplitude(value,channel)
    #    elif param == "offset":    self.setOffset(value,channel)
    #    else:  logger.warning(f"Unknown parameter:{param} with value={value}")


    ######################################
    #     Hanlding channel 
    #       0: channel 1
    #       1: channel 2 
    #      -1: both channel (=3)
    ######################################

    def getChannel(self,ch): return 3 if (ch==-1 or ch>2) else ch+1

    ######################################
    #     Generic parameter interface
    ######################################
        
     
    def extractParameterResult(self,responce,no):
        res =  None if responce is None else responce.getParams().split(":")
        return res[no] if res and len(res)>no else None
    
    def getParametersCount(self,ch=0):
        res = self.genericRequest ( Cmd.Request( f">{ch}:p:c" ) )
        try: 
            cnt = int( self.extractParameterResult( res , 2) )
        except:
            cnt  = 0
            logger.error(f"Read cuond not voncert parameters of current mode @channel {ch} to int (res:{res})")
        logger.info(f"Read count={cnt} for parameters of current mode @channel {ch} (res:{res})")
        return cnt


    def getParameterProperties(self,par,ch=0):
        prop = {}        
        prop['name']  = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:n:{par}" ) ) , 2) ; 
        prop['unit']  = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:u:{par}" ) ) , 2) ; 
        prop['type']  = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:t:{par}" ) ) , 2) ; 
        prop['max']   = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:a:{par}" ) ) , 2) ; 
        prop['min']   = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:i:{par}" ) ) , 2); 
        prop['step']  = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:s:{par}" ) ) , 2); 
        prop['value'] = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:p:v:{par}" ) ) , 2); 
        logger.debug(f"Read parameter i={par} of current mode @channel {ch} : {prop}")
        return prop
        
    def getParametersProperties(self,ch=0):
        cnt = self.getParametersCount(ch)
        params = []
        for no in range(cnt):
            params.append( self.getParameterProperties(no,ch) )
        logger.info(f"Read {cnt} parameters of current mode @channel {ch}")
        logger.debug(f"{params}")
        return params

    def setParameter(self,no,val,ch=0):
        responce = self.genericRequest ( Cmd.Request( f">{ch}:p:{no}:{val}" ))
        logger.info(f"Set parameter{no} = {val} @channel:{ch} (result={responce})")
        return responce
    
    ######################################
    #     Mode function
    ######################################

            
    def getMode(self,ch=1):
        responce = self.genericRequest ( Cmd.Request( f">{ch}:o" ))
        mode = self.extractParameterResult( responce, 1)
        try:        
            mode = int( mode )
        except:
            logger.error(f"Could not convert {mode} to int @channel (responce: {responce})")
            mode = 0
        logger.info(f"Mode of channel {ch} read: {mode} ({responce})")
        return mode

    def setMode(self,mode,ch=1):
        responce = self.genericRequest ( Cmd.Request( f">{ch}:o:{mode}" ))
        logger.info(f"Mode of channel {ch} set to {mode} = {responce}")
        return responce       
    
    def getModeProperties(self,par,ch=1):
        prop = {}
        prop['name']  = self.extractParameterResult( self.genericRequest ( Cmd.Request( f">{ch}:n:{par}" ) ) , 1)
        logger.info(f"Mode {par} name @channel {ch} = {prop}")
        return prop        
    
    def getModesCount(self,ch=1):
        res = self.genericRequest ( Cmd.Request( f">{ch}:c" ) )
        try:        
            cnt = int( self.extractParameterResult( res , 1) )
        except:
            cnt = 0
            logger.error(f"Error converting mode count to int: channel:{ch} result:{res})")
            
        logger.info(f"Mode count of channel {ch} is {cnt} (result: {res})")
        return cnt
    
    
    def getModesProperties(self, ch=1):
        cnt = self.getModesCount(ch)
        modes = []
        for no in range(cnt):
            modes.append( self.getModeProperties(no,ch) )
        return modes

    



    
    
def main():
    
    print("Not a runnable code, use FcnGenGUI or FcnGenCMD to start a running program")

        
    
if __name__ == '__main__':
    proc = main()