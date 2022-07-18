# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 21:42:20 2022

@author: pagan
"""

from FcnGen import *

import logging
logger = logging.getLogger(__name__)     


class FcnGenCMD:
    pass
    
    

def main():
    
    
    
    #logging.basicConfig(level=logging.INFO)
    #logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    print("FcnGen2 Command Line Interface")
    print(" (type h or help for help)")
    
    fcnGen = FcnGen(port="COM12",baudrate=115200)
    #fcnGen = FcnGen(IP="192.168.0.195")
    if not fcnGen.connect(): 
        logger.error("could not connect, exiting")
        return
        
    
    fcnGen.add_subscription(lambda x: print("--> " , x),"*",True)
    
    
    # >> if connected // ! if not connected

    try:
     while True:
        text = input(">> ")
        
        if text == "q": break;
        elif text == "parlist": 
            parList = fcnGen.getParametersProperties()
            print("Parameter List: ")
            for i,p in enumerate(parList): print(f" {i:2d} : {p}") 
        elif text == "modes": 
            modeList = fcnGen.getModesProperties()
            print("Mode List: ")
            for i,p in enumerate(modeList): print(f" {i:2d} : {p}") 
        elif text == "buffer": 
            buf = fcnGen.getUnhandledResponces()
            for i,b in enumerate(buf): print(f" {i:2d} : {b}") 
        else:
            res = fcnGen.genericRequest(text)       
            print("user cmd : ",text)
            print("result   : ",res)
    finally:
      fcnGen.disconnect(); 

    
#    fcnGen.setFrequency(1000)      
#    fcnGen.setOffset(842)
#    fcnGen.setGain(128);


        
if __name__ == '__main__':
    proc = main()