# -*- coding: utf-8 -*-
"""
Created on Mon May 23 21:36:08 2022

@author: pagan
"""


import socket


import my_logger
logger = my_logger.get_logger(__name__)

from FcnGenInterface import FcnGenInterface



class FcnGenInterfaceETH (FcnGenInterface):

    def __init__(self,IP=None, port=None):
        self.IP=IP
        self.port=port
        super().__init__()
        pass
    
    def connect(self,IP=None,port=None):
        logger.info("Connecting to ethernt interface")
        if(self.s is not None): self.close()
        if(port is None): port=self.port;
        if(IP is None): IP= self.IP
        if(port is None): port=2000

        try:
            logger.debug(" IP=%s:%d" % (IP,port))
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(60)
            self.s.connect((IP,port ))
            logger.debug(" connected successfully")
        except TimeoutError: #socket.timeout:
            logger.debug(" timeout occured")
            self.s.close()    
            return False
        except  ConnectionRefusedError: #socket.timeout:
            logger.debug(" connection refused")
            self.s.close()    
            return False
        return True   

    def write(self,cmd):
        if self.s is not None: 
           self.s.send(cmd); #print("Send: ",cmd)
        else: 
           logger.warning("writing to not connected ethernet interface")
        #self.s.write(cmd)     # write a string
        #self.s.flush()

        
    def read(self):
        if self.s is None: return None
        try:
            data = self.s.recv(4096)
            if not data:
                print("disconnected from server")
                return False;
            return data
        except socket.timeout:
            return None
        except ConnectionResetError:
            print("Connection broken")
            return False;
        