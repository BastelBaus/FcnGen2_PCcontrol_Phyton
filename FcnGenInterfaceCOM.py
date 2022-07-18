# -*- coding: utf-8 -*-
"""
Created on Mon May 23 21:38:26 2022

@author: pagan
"""

import serial
import time   # for sleep


import my_logger
logger = my_logger.get_logger(__name__)

# logging low level serial communication to a file
comFileLogger = my_logger.get_fileLogger(__name__)

        
from FcnGenInterface import FcnGenInterface

class FcnGenInterfaceCOM(FcnGenInterface):
    """ implements the serial interface functions """
    
    
    WAIT_TIME = 1               # in seconds between two connection attemps
    TIMEOUT   = 0.005           # timout setting of the com interface 
    
    def __init__(self,port=None,baudrate=115200):
        self.port=port
        self.baudrate=baudrate
        super().__init__()
    
    def releaese(self):
        super().release()
        logger.error("del IF_COM")

    def __hasConObj(self):
        """ returns true if the con object s can be accessed """
        return hasattr(self,"s") and self.s is not None            
        
    def disconnect(self):
        logger.error("disconnect IF_COM")
        """ disconnect from port """ 
        if self.__hasConObj(): 
            self.s.close()
            del self.s
            logger.error("disconnected serial port")
        
    def isConnected(self): 
        """ returns true if connected """ 
        if self.__hasConObj(): return self.s.isOpen()
        return False
    

    def connect(self,port=None,baudrate=None):
        """ connect to serial port, tries it twice """ 
        
        logger.info("Connecting to serial interface")
        if self.__hasConObj(): self.disconnect(); time.sleep(0.5);
        if(port is None): port=self.port;
        if(port is None): logger.warning("No port given, returning w/o connecting (port=%s,baudrate=%d)"%(port,baudrate));  return;        
        if(baudrate is None): baudrate=self.baudrate;
        
        # first try
        try:
            logger.debug(" port=%s,baudrate=%d"%(port,baudrate) )
            self.s = serial.Serial(port,baudrate)
            self.s.timeout = FcnGenInterfaceCOM.TIMEOUT
            logger.debug(" successfull")
            return True
        except serial.SerialException:
            logger.debug(" failed, trying a second time after %d seconds" % (self.wait_time))

        # try it a second time :-)        
        time.sleep(FcnGenInterfaceCOM.WAIT_TIME);
        try:
            logger.debug(" port=%s,baudrate=%d"%(port,baudrate) )
            self.s = serial.Serial(port,baudrate)
            self.s.timeout = FcnGenInterfaceCOM.TIMEOUT
            logger.debug(" successfull")
            return True
        except serial.SerialException as e:
            logger.warning("Error connecting to port: " + str(e))
        
        return False
            

    def write(self,cmd):
        """ writes data to the com port """
        if self.__hasConObj():
            comFileLogger.info(f"w:{cmd}")
            self.s.write(cmd)     # write a string
            self.s.flush()
        else: logger.error(f"writing {cmd} to not connected interface")
        
        
    def read(self):
        """ reads data to the com port """
        if not self.__hasConObj():
            #logger.warning("reading from a not connected interface")
            return None
        try:
            cmd = self.s.read(size=40)
            #s = self.s.read_until(b'\n',40) 
            if cmd == b'': return None
            comFileLogger.info(f"r:{cmd}")
            return cmd
        except serial.SerialTimeoutException:
            return None
        except serial.SerialException:
            return None
        #except ctypes.ArgumentError:
        except:
            return None
        