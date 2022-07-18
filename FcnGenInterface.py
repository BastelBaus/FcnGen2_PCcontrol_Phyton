# -*- coding: utf-8 -*-
"""
Created on Mon May 23 20:35:22 2022

@author: pagan
"""


from threading import Thread, Lock
import time # for sleep
import Command

import my_logger
logger = my_logger.get_logger(__name__)

# logging low level communication protocol to a file
IFFileLogger = my_logger.get_fileLogger(__name__)

class FcnGenInterface(Thread):
    
    def __init__(self):
        super().__init__()
        self.data = b''  # a line read from the interface
             
        self.sendListener = None

        self.responceBuffer = []
        self.subscriber = []
        
        self.send_lock = Lock()
        self.data_lock = Lock()
        self.runReadThread = True
        self.start() # start reading thread
        self.name = "FcnGenIF" # thread name
        logger.info("Initialized FcnGenIF and started as thread")        

        
    def release(self):
       logger.error("del IF")
       self.responceBuffer = []
       self.runReadThread = False
       self.raise_exception() # raise thread exection to stop loop
       logger.error("Yes, raised exception") 
       logger.info("Closed FcnGenIF and stoped thread")    


    
    def getUnhandledResponces(self):
        return self.responceBuffer
        
    def installSendListener(self,call):
        self.sendListener = call

    # directly sent a command to the interface
    def __sendln(self,cmd):
        strCMD = cmd.getByteStingCommand();
        if self.sendListener is not None: self.sendListener( strCMD )        
        self.write( strCMD )
        IFFileLogger.info(f"s: {strCMD}")
        
    def queryln(self,cmd):
        with self.send_lock:
            self.__sendln( cmd )
            logger.debug("SEND @ " + str(time.time()) + " >" + str(cmd) + "<")
            
            
            MAXTIME = 2
            STARTTIME = time.time()
            
            logger.debug("waiting to receive >" + cmd.getCommandCode() + "< from the responce buffer")        
            while (time.time() - STARTTIME) <  MAXTIME:
                for i,responce in reversed(list(enumerate(self.responceBuffer))):
                    if cmd.isValidResponce(responce): 
                        with self.data_lock:
                            tmp = self.responceBuffer[i]
                            del self.responceBuffer[i]
                            logger.debug("  Found responce: " + str(tmp))
                            return tmp
                    #else: time.sleep(0.001)
                
            
            logger.warning("Timeout, did not get any responce to >" + str(cmd) + "<")  
            logger.debug("    responce buffer: " + str( len(self.responceBuffer) ) )
            for i,responce in enumerate(self.responceBuffer):
                #logger.debug("  " + str(i) + "=  b=" + str(b) + "  c1:" + str(c1) + " c:" + str( c.encode()))
                logger.debug(f"    {i:2d}=  " + str(responce))
            return Command.NoResponce()
  
            
    def isConnected(self): 
       """ abstractmethod, implenet!! ToDO """
       return False;

    def run(self):
        """ endless loop reading from interface and pushing new 
            commands to the command queue. Inherited from Thread.
        """
            
        try:
          while self.runReadThread:
            #if not self.isConnected(): continue
            #if (ret := self.__readln() ) is not None:
            if self.isConnected() and (ret := self.__readln() ) is not None:
                with self.data_lock:
                    self.__new_command(Command.Responce(ret))
        finally: logger.error("Ended reading thread")   
                    
                    
    def __readln(self):
        """ reads data from teh interface until a full 
            command was received and then returns the full command
        """        
        
        # extract single command from queue
        def getSingleCommand():
            if b'\n' in self.data:
                cmd,self.data = self.data.split(b'\n',1)
                IFFileLogger.info(f"r: {cmd}")                                   
                return cmd;
            return None
        
        # if buffer has commands left, directly return them
        if (cmd:=getSingleCommand()) is not None: return cmd
        
        # read until first command is available
        while True:
            k = self.read()
            if k is None: continue
            self.data = self.data + k            
            if (cmd:=getSingleCommand()) is not None: return cmd
        
            
    # for each new command, check and feed subscribers and
    #  push the commands to the stack eventually
    def __new_command(self,cmd):
        c = cmd.getCommandCode()
        logger.debug(f"CommandID: {c} of command: {cmd}")
        logger.debug("Checking all subscribers: " + str(len(self.subscriber)))
        # go through all subsribers
        for i,sub in enumerate(self.subscriber):
            logger.debug(f"  .. subscriber {i} cmd:" +  str(sub["cmd"]) + "  consumer:" + str(sub["consumer"]) )
            if (sub["cmd"] is None) or (c == sub["cmd"]): 
                if callable(sub["call"]):
                       logger.debug("   -> Calling: " + str(sub["call"].__name__) + " with argument: " + str(cmd))
                       sub["call"]( cmd )
                       #th = Thread(target=sub["call"],args=(cmd,)).start()
                       
                else:  logger.waring("Subscriber call: " + str(sub["call"]) + " not callable")
                if  sub["consumer"]: 
                    logger.debug("   -> Subscriber was consumer and consumed the command, not putting to buffer")
                    return            
        # if not consumed, put command to the buffer
        sz = len(self.responceBuffer)
        #for i,s in enumerate(self.responceBuffer): print(i,': ',s)
        logger.debug(f"adding >{cmd}< to buffer with size >{sz}<")
        self.responceBuffer.append(cmd)
                
    # if CMD, call for every function, else only if mathcing
    def add_subscription(self,call,cmd,consumer=False):
        self.subscriber.append( { "call":call,"cmd":cmd,"consumer":consumer } )
        logger.debug("Adding a subscriber, now with " + str(len(self.subscriber)) + " elements")
            

        
    
if __name__ == '__main__':
    pass    
        