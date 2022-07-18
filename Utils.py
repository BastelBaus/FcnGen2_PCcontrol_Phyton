# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 23:02:58 2022

@author: pagan
"""

import time
import psutil    
import threading 

def TicTocGenerator():
    # Generator that returns time differences
    ti = 0           # initial time
    tf = time.time() # final time
    while True:
        ti = tf
        tf = time.time()
        yield tf-ti # returns the time difference

TicToc = TicTocGenerator() # create an instance of the TicTocGen generator

# This will be the main function through which we define both tic() and toc()
def toc(tempBool=True):
    # Prints the time difference yielded by generator instance TicToc
    tempTimeInterval = next(TicToc)
    if tempBool:
        print( "Elapsed time: %f seconds.\n" %tempTimeInterval )

def tic():
    # Records a time in TicToc, marks the beginning of a time interval
    toc(False)
    
    
    
def isInt(x):
    try:
        int(x)
        return True
    except ValueError:
        return False
    

def setTerminalWidth():
    #from shutil import get_terminal_size
    #pd.set_option('display.width', get_terminal_size()[0])
    pass

# 
def countThreads():
  return threading.active_count()

def printAllThreads():
    for thread in threading.enumerate(): 
        print(thread.name)
  
def listProcesses():
    '''
    Get a list of all the PIDs of a all the running process whose name contains
    the given string processName
    '''
    listOfProcessObjects = []
    for proc in psutil.process_iter():
       try:
           pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
           listOfProcessObjects.append(pinfo)
           print(pinfo)
           # Check if process name contains the given name string.
       except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
           pass
    return listOfProcessObjects;