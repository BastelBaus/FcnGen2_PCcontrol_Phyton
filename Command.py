# -*- coding: utf-8 -*-
"""
Created on Thu May 26 21:07:22 2022

@author: pagan
"""

from Utils import isInt 




class Command:

    def __init__(self,cmd):
        self.cmd = Command.unify(cmd)
    
    def unify(cmd):        
        if type(cmd) == type(b''): cmd = cmd.decode(errors='ignore')
        else: cmd = str(cmd)
        cmd = cmd.replace("\n","")
        cmd = cmd.replace("\r","")
        return cmd
        
    def __str__(self): return self.cmd
    
    def isValid(self): return False
    def isOK(self): return False

    
    def getCommandCode(self):
        if self.isValid(): 
            c,*stat = self.cmd.split(":");     
            return c        
        return None
        
    def getByteStingCommand(self):
        if not self.isValid(): return ""
        return (self.cmd + "\n").encode()
    def getStingCommand(self):
        if not self.isValid(): return ""
        return (self.cmd + "\n").encode()


        
class NoResponce(Command):
    def __init__(self):
        super().__init__("")
    
    def __str__(self): return "no valid responce\n"


class Responce(Command):
    
    def __init__(self,cmd):
        super().__init__(cmd)
        
    
    def isValid(self):
        if self.cmd is None:     return False
        if self.isDebugMsg():    return True
        if self.isErrorMsg():    return True
        if self.isInfoMsg():     return True
        if self.isWatchdogMsg(): return True
        
        # other command have teh form "cmd:stat(:others)
        c,*stat = self.cmd.split(":");     
        if (len(stat)==0): return False
        c,stat,*opt = self.cmd.split(":");     
        if   stat == "OK" : return True
        elif stat == "ERR": 
            if len(opt)==0 or (not isInt(opt[0])) : return False
            else: return True
        else: return False
        

    def isDebugMsg(self): return (len(self.cmd)>0) and (self.cmd[0]=="*")
    def isInfoMsg(self):  return (len(self.cmd)>0) and (self.cmd[0]=="?")
    def isErrorMsg(self): return (len(self.cmd)>0) and (self.cmd[0]=="#")
    def isWatchdogMsg(self): return (len(self.cmd)>1) and (self.cmd[0]=="!") and (self.cmd[1]=="a")
        
    def isOK(self):
        if not self.isValid(): return False
        c,stat,*_ = self.cmd.split(":");     
        return stat == "OK"

    def isError(self): return self.isValid and (not self.isOK()) and (not self.isDebugMsg()) and (not self.isErrorMsg()) and (not self.isInfoMsg())

    
    def getErrorCode(self): 
        if self.isOK() or self.isDebugMsg() or self.isErrorMsg() or self.isInfoMsg(): return None
        c,stat,errno, *_ = self.cmd.split(":");     
        return int(errno)
        
    def getParams(self):
        if self.isOK(): 
            c,stat,*par = self.cmd.split(":");     
        elif self.isError(): 
            c,stat,errno, *par = self.cmd.split(":");
        elif self.isDebugMsg(): return self.cmd[1:]
        elif self.isErrorMsg(): return self.cmd[1:]
        elif self.isInfoMsg():  return self.cmd[1:]
        else: par = []
        return ":".join(par)


    # overloaded to handle debug responces from slave
    def getByteStingCommand(self):
        if self.isDebugMsg():   return "*"
        elif self.isInfoMsg():  return "?"
        elif self.isErrorMsg(): return "#"
        else:                   return super().getByteStingCommand()

    def getCommandCode(self):
        if self.isDebugMsg():   return "*"
        elif self.isInfoMsg():  return "?"
        elif self.isErrorMsg(): return "#"
        else: return super().getCommandCode()
        

class Request(Command):
        
    
    def __init__(self,cmd):
        super().__init__(cmd)
        
    
    def isValidResponce(self,cmd):
        #print(self.getCommandCode()," == ",Responce(cmd).getCommandCode())
        return self.getCommandCode() == Responce(cmd).getCommandCode()
     
    def isOK(self): return self.isValid()

    def isValid(self):
        if self.cmd is None: return False
        if len(self.cmd) < 2: return False
        return True



