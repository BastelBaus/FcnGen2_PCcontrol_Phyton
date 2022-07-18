

# generic libraries
import tkinter.ttk as tk
import tkinter as tk

from dataclasses import dataclass,field
from functools import partial
from threading import Thread, Lock
import copy


from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

# own libraries
from FcnGen import FcnGen
import FcnGenInterface
import configuration as cfg
from Utils import *

import my_logger
logger = my_logger.get_logger(__name__)   




MAX_LAST_CONNECTION_ENTRIES = 6

    

def donothing(x=None):
    print('nothing: ' + str(x) )


NONE_DISABLE_WIDGETS = ('Frame','Labelframe','TNotebook','TFrame','NoneType')
def disableChildren(parent):
    if parent.winfo_class() not in NONE_DISABLE_WIDGETS: parent.configure(state='disable')    
    else:
        for child in parent.winfo_children():
            wtype = child.winfo_class()
            if wtype not in NONE_DISABLE_WIDGETS:
                child.configure(state='disable')
            else:
                disableChildren(child)

def enableChildren(parent):
    if parent.winfo_class() not in NONE_DISABLE_WIDGETS: parent.configure(state='normal')    
    else:
        for child in parent.winfo_children():
            wtype = child.winfo_class()
            if wtype not in NONE_DISABLE_WIDGETS:
                child.configure(state='normal')
            else:
                enableChildren(child)

            
@dataclass
class param:
    name:     str = ""
    unit:     str = ""
    limits:   tuple = (0,0)
    call:     object = None
    strValue: object = None 
    
@dataclass
class sigType:
    name:   str = ""
    params: list = field(default_factory=lambda: [])    
    call:   object = None
    def __str__(self):
        return self.name
    
@dataclass
class channelType:
    signals: list = field(default_factory=lambda: [
                      sigType('sin',      [ param('A','V', (0,0.3),   call=lambda x,y,z: FcnGen.setAmplitude(x,y,z) ),
                                            #param('O','V', (-16,15), call=lambda x,y,z: FcnGen.setOffset(x,y,z) ),
                                            param('O','V', (0,2048), call=lambda x,y,z: FcnGen.setOffset(x,y,z) ),
                                            param('F','Hz',(0,5e6),  call=lambda x,y,z: FcnGen.setFrequency(x,y,z) ),
                                           ], lambda x,y: FcnGen.setSinus(x,y)      ) , 
                      sigType('triangle', [ param('A','V', (0,0.3),   call=lambda x,y,z: FcnGen.setAmplitude(x,y,z) ),
                                            param('O','V', (-16,15), call=lambda x,y,z: FcnGen.setOffset(x,y,z) ),
                                            param('F','Hz',(0,5e6),  call=lambda x,y,z: FcnGen.setFrequency(x,y,z) ),
                                           ], lambda x,y: FcnGen.setTriangle(x,y) ) , 
                      sigType('square',   [ param('A','V', (0,0.3),   call=lambda x,y,z: FcnGen.setAmplitude(x,y,z) ),
                                            #param('O','V', (-16,15), call=lambda x,y,z: FcnGen.setOffset(x,y,z) ),
                                            param('O','V', (0,2048), call=lambda x,y,z: FcnGen.setOffset(x,y,z) ),
                                            param('F','Hz',(0,5e6),  call=lambda x,y,z: FcnGen.setFrequency(x,y,z) ),
                                           ], lambda x,y: FcnGen.setSquare(x,y)   ) 
                    ])



def validateFloat(x):
    try:  
        float(x)
        return True
    except ValueError: return False

NO_OF_CHANNELS = 2

class FcnGenGUI(FcnGen):
    
    def __init__(self):
        self.main = tk.Tk()
        self.main.lift()
        self.main.title('FcnGen')
        
        self.commandHistory   = []
        self.commandHistoryID = 0
      
        self.channels = [ channelType(), channelType() ]
        
        stat = cfg.readStr("connections","last0") 
        stat = stat if stat not in ['',None] else "-None-" 
        self.currentConnection = tk.StringVar(value=stat  )
        
        self.signaltype = [ tk.StringVar(value=""), tk.StringVar(value="") ]
        self.tabControl = [None,None]
        
        #self.outputModes = ['Mode1','Mode2','Mode3','Mode4']        
        #self.outputMode = [ tk.StringVar(value=self.outputModes[0]), tk.StringVar(value=self.outputModes[0]) ]
        self.outputMode = [ tk.StringVar(value=""), tk.StringVar(value="") ] # selected output mode per channel
        self.sigModeOptionMenu = [None,None]
        self.valVar = [None,None]
        
        self.modeParameterFrame = [None,None]
        
        
        self.commandString = tk.StringVar(value="");
        
        self.lastWdtCall = 0
        
        #tk.ttk.Style().layout('TNotebook.Tab', []) # turn off tabs
    
        self.floatValidator = self.main.register(validateFloat)                
        self.data_lock = Lock()

        self.limits = {'sin':{'A':[None,None],'O':[None,None],'F':[None,None]},
                       'triangle':{'A':[None,None],'O':[None,None],'F':[None,None]},
                       'square':{'A':[None,None],'O':[None,None],'F':[None,None]}
                       }
        #self.limits = {}
            
        super().__init__()
        
      
        
    def __del__(self):
        self.close()
        super().__del__()
        
        
    def close(self):
        super().close()
        self.running = False
        
        self.disconnect()       
        try: 
            self.main.destroy()
            logger.debug("destroyed window successfully")
        except:
            logger.debug("destroyed window failed, might already be closed")
        #if hasattr(self,'main') and self.main and self.main.winfo_exists(): self.main.destroy()
        
        
    def setDisConnected(self):
        self.disableOnNotConnected()
    
    def enableOnConnected(self):
        
        # Note: Order matters if "True" since responces gets removed
        self.add_subscription(lambda x: self.addStatusLine(str(x),'grey') ,"*",True)
        self.add_subscription(lambda x: self.addStatusLine(str(x),'red')  ,"#",True)
        self.add_subscription(lambda x: self.addStatusLine(str(x),'blue') ,"?",True)
        #self.add_subscription(lambda x: self.addStatusLine(str(x),'red') ,"!a",True) # watchdog
        self.add_subscription(lambda x: self.handleConnectionWatchdog() ,"!a",True) # watchdog
        self.add_subscription(lambda x: self.addStatusLine(str(x),'black') ,None,False)
        if self.frameMiddleConfig.winfo_ismapped(): self.readConfigValues()
        
        enableChildren(self.rebootButton)
        enableChildren(self.frameMiddleControl)
        for k in [0,1,2]: enableChildren(self.confFrame[k])
        enableChildren( self.confFrameSave ) 
        enableChildren( self.confFrameReLoad ) 
        enableChildren(self.commandEntry)
        self.connectButton.config(bg="green")
        
        self.readModeConfiguration()

    def disableOnNotConnected(self):
        disableChildren(self.rebootButton)
        disableChildren(self.frameMiddleControl)
        for k in [0,1,2]: disableChildren(self.confFrame[k])
        disableChildren(self.confFrameSave ) 
        disableChildren(self.confFrameReLoad ) 
        disableChildren(self.commandEntry)
        self.connectButton.config(bg="red")

    def tryToConnect(self, toggle=False):
        logger.info("TryToConncet - toggle= " + str(toggle) )
        if toggle and self.isConnected():
            logger.debug("Disconnecting" )
            self.disconnect()
            self.disableOnNotConnected()
        else:
            conStr = self.currentConnection.get()
            logger.info("Connecting to " + conStr )
            # to do: do her ethernet and serial
            a = conStr.split('@')
            if self.connect(port=a[0],baudrate=int(a[1])) :
                if not self.checkAlive(): 
                    logger.info(" ... device not alive")
                    return;
                self.addStatusLine(f"connected successfully to {conStr}","black")
                logger.info(" ... successfull")
                

                self.enableOnConnected()
                
                # self.checkDebug() # get some messages from slave to debug the GUI output
                
            else: logger.info(" ... failed")

        
    def handleConnectionWatchdog(self):
        logger.debug("Watchdog received")
        
        
    def menuConnectSerial(self,conStr=None):
        if conStr is None: conStr = self.comport.get() + "@" + str(self.baudrate.get())
        logger.info("Connect on " + conStr)
        cfg.pushStr("connections","last",conStr,maxItems = MAX_LAST_CONNECTION_ENTRIES )       
        self.currentConnection.set(conStr)
        #self.serial.destroy()
        if hasattr(self, 'serial'): self.serial.destroy()
        self.tryToConnect()        
        self.updateConnectionMenu()
 
    def menuConnectEthernet(self,conStr=None):
        if conStr is None: conStr = self.ip.get() + "@" + self.ethport.get()
        logger.info("Connect on " + conStr)
        cfg.pushStr("connections","last",conStr,maxItems = MAX_LAST_CONNECTION_ENTRIES )       
        self.currentConnection.set(conStr)
        #self.serial.destroy()
        if hasattr(self, 'ethernet'): self.ethernet.destroy()
        self.tryToConnect()        
        self.updateConnectionMenu()
 
        
    def ethernetDialog(self):
        #get some parameters
        ethports = "" # self.getListOfCOMPorts()
        address  = "" # self.getListOfCOMBaudrates()                
        
        # create dialog window
        self.ethernet = tk.Toplevel(self.main)
        self.ethernet.grab_set()
        self.ethernet.title('Connect on ethernet')
        
        # create variables
        self.ip = tk.StringVar(self.ethernet)
        self.ip.set("") 
        self.ethport  = tk.StringVar(self.ethernet)
        self.ethport.set("")

        # layout dialog
        prt = tk.Entry(self.ethernet, textvariable=self.ip)
        brd = tk.Entry(self.ethernet, textvariable=self.ethport)
        con = tk.Button(self.ethernet, text="Connect", command=self.menuConnectEthernet)
        can = tk.Button(self.ethernet, text="Cancel", command=self.ethernet.destroy)
        prt.grid(column=0,row=0,sticky='nwes')
        brd.grid(column=1,row=0,sticky='nwes')
        can.grid(column=0,row=1,sticky='nwes')
        con.grid(column=1,row=1,sticky='nwes')

    
    def serialDialog(self):
        
        #get some parameters
        comports   = self.getListOfCOMPorts()
        baudrates  = self.getListOfCOMBaudrates()                
        if len(comports)<1 or len(baudrates)<1:
            logger.error("no comport available")
            return
        
        # create dialog window
        self.serial = tk.Toplevel(self.main)
        self.serial.grab_set()
        self.serial.title('Connect on serial')
        
        # create variables
        self.baudrate = tk.IntVar(self.serial)
        self.baudrate.set(baudrates[-1]) 
        self.comport  = tk.StringVar(self.serial)
        self.comport.set(comports[0])

        # layout dialog
        prt = tk.OptionMenu(self.serial, self.comport, *comports)
        brd = tk.OptionMenu(self.serial, self.baudrate, *baudrates)
        con = tk.Button(self.serial, text="Connect", command=self.menuConnectSerial)
        can = tk.Button(self.serial, text="Cancel", command=self.serial.destroy)
        prt.grid(column=0,row=0,sticky='nwes')
        brd.grid(column=1,row=0,sticky='nwes')
        can.grid(column=0,row=1,sticky='nwes')
        con.grid(column=1,row=1,sticky='nwes')

    # create all elements from main frame
    def create(self):
        self.createMainAreas()
        self.createMenu()
        self.disableOnNotConnected()
        
         
    # change sin, triangle, ...
    def changeSignalMode(self, channel, nbook, mode):
        cid = channel-1
        tid = [ str(i) for i in self.channels[cid].signals ].index(mode.get())        
        nbook.select(tid)
        self.channels[cid].signals[tid].call(self,channel)
        logger.info("change to " + mode.get() + "(" + str(tid) + ") for channel:" + str(channel) )
        

 

    def showControlArea(self):
        self.frameMiddleConfig.grid_remove()
        self.frameMiddleControl.grid(row=1,column=0,sticky = 'ew')
    
    def showConfigArea(self):
        self.frameMiddleConfig.grid(row=1,column=0,sticky = 'ew')
        self.frameMiddleControl.grid_remove()        
        self.readConfigValues()
    
    def readConfigValues(self):
        for ch in [0,1,2]:            
            for widget in self.confFrame[ch].winfo_children(): widget.destroy()
        self.configParameters = {}
        if not self.isConnected(): return
    
        self.addStatusLine("Reading configuration values, might take some time ...","black")
        for ch in [0,1,2]:            
            chCfg= self.getChannelConfig(ch) 
            logger.info(f"channel:{ch} get parameters: " + str(chCfg))
            for i,parID in enumerate(chCfg):
                par = self.getParameter(parID)
                self.configParameters[parID] = tk.StringVar()
                self.configParameters[parID].set(par[0])
                logger.info(f"{parID}: {par}")
                tk.Label(self.confFrame[ch],text=par[1]).grid(column=0, row=i)
                e = tk.Entry(self.confFrame[ch],width=8,textvariable=self.configParameters[parID])
                #e = tk.Entry(self.confFrame[ch],width=8)
                #e.insert(tk.END, par[0])
                e.grid(column=1, row=i)
                tk.Label(self.confFrame[ch],text=par[2]).grid(column=2, row=i)
        self.addStatusLine(" ... done","black")
         
    def writeConfigValues(self):
        logger.info("Writing all configf variables")        
        for k in self.configParameters:
            par = self.configParameters[k].get()
            self.writeParameter(k,par)
            logger.debug(f"write {par} to {k}")            
        self.readConfigValues()
    
    # create main layout and call functiosn to create sub layouts
    def createMainAreas(self):
        self.frameTop     = tk.Frame(self.main, relief=tk.RAISED, borderwidth=1)
        self.frameMiddleControl = tk.Frame(self.main, relief=tk.RAISED, borderwidth=1)
        self.frameMiddleConfig  = tk.Frame(self.main, relief=tk.RAISED, borderwidth=1)
        self.frameBottom  =  tk.Frame(self.main, relief=tk.RAISED, borderwidth=1)
        self.frameTop.grid(row=0,column=0,sticky = 'ew')
        self.frameBottom.grid(row=2,column=0,sticky = 'ew')
        self.showControlArea()
        
        self.createConnectionFrame(self.frameTop)
        self.createConfigFrame(self.frameMiddleConfig)
        self.createControlFrame(1,self.frameMiddleControl)
        self.createControlFrame(2,self.frameMiddleControl)
        self.createStatusTextFrame(self.frameBottom)
    
    # create top most frame with information on connection status
    def createConnectionFrame(self,parent):
        self.connectButton        = tk.Button(parent, text ="Connect", command = lambda: self.tryToConnect(True) )
        self.connectButton.pack(side=tk.LEFT)
        
        tk.Label(parent,textvariable= self.currentConnection ).pack(side=tk.LEFT)
        
        self.rebootButton   = tk.Button(parent, text ="REBOOT device", command = self.doReboot)
        self.rebootButton.pack(side=tk.RIGHT)
        
    # create frame with subframes showing all configuration parameters
    def createConfigFrame(self, parent):
        self.confFrame = []
        
        self.confFrame.append( tk.LabelFrame(parent, text="Channel1", relief=tk.RAISED, borderwidth=1) )
        self.confFrame[0].pack(side=tk.LEFT,fill=tk.BOTH)
        #tk.Label(self.confFrame[0],text="test1").pack()
        
        self.confFrame.append( tk.LabelFrame(parent, text="Channel2", relief=tk.RAISED, borderwidth=1) )
        self.confFrame[1].pack(side=tk.LEFT,fill=tk.BOTH)
        #tk.Label(self.confFrame[1],text="test2").pack()
        
        self.confFrame.append( tk.LabelFrame(parent, text="Generic", relief=tk.RAISED, borderwidth=1) )
        self.confFrame[2].pack(side=tk.LEFT,fill=tk.BOTH)
        #tk.Label(self.confFrame[2],text="test3").pack()
        
        self.confFrameSave   = tk.Button(parent, text="save",   command=self.writeConfigValues)
        self.confFrameSave.pack(side=tk.BOTTOM)
        self.confFrameReLoad = tk.Button(parent, text="reload",   command=self.readConfigValues)
        self.confFrameReLoad.pack(side=tk.BOTTOM)
        tk.Button(parent, text="cancel", command=self.showControlArea).pack(side=tk.BOTTOM)
        
        
    def setOutputMode(self,mode,ch,modes):
        """ set the output mode of a channel.
            Mode is the id of current selected mode and
            modes is the list of all mode names
        """
        logger.info(f"Set output mode {mode} of channel {ch} (available: {modes})")     
        cid = ch+1
        self.setMode(mode,cid) # set to slave
        self.outputMode[ch].set(modes[mode]) # set widget
        self.readParameterConfiguration(ch) # update parameters


    # change parameters of a signal
    def changeSignalParams(self,channel, param):
        if param.call is not None: 
            param.call(self, param.strValue.get(), channel)
        logger.info("change " + str(param) + " @ channel:" + str(channel) )

    def changeParameter(self,i,ch):
        #if param.call is not None: 
        #    param.call(self, param.strValue.get(), channel)
        #logger.info("change " + str(param) + " @ channel:" + str(channel) )
        cid = ch + 1
        logger.info(f"Set parameter:{i} of channel {cid} ({ch}) ")   
        val = self.valVar[ch][i].get()
        self.setParameter(i,val,cid) 
        logger.info(f"Set parameter:{i} of channel {cid} to {val} ")     
        
        
    def readParameterConfiguration(self,ch):
        """ read all parameters for current mode and re-create widget """
        
        cid = ch + 1 
        logger.info(f"Reading parameter configurations of channel {cid}")     
        props = self.getParametersProperties(cid)
        #self.sigModeOptionMenu[ch]['menu'].delete(0, "end") # delete widtget content
        
        # clear old paramters
        for widget in self.modeParameterFrame[ch].winfo_children(): widget.destroy()
        self.valVar[ch] = []
                
        logger.info("Creating new widget content for parameters")     
        for i,prop in enumerate(props):
            #def createControl():
            logger.debug(f"Parameter {i} with props : {prop}")            
            frm = self.modeParameterFrame[ch] # just a shortcut
            
            self.valVar[ch].append(tk.StringVar(frm, value=prop['value']) )
            #self.valVar[ch][i].trace("w", lambda name, index, mode, c=ch, p=prop, ii=i: print("Set new val: ",c," ", p," ",ii))            
            #self.valVar[ch][i].trace("w", lambda name, index, mode, c=ch, v= self.valVar[ch][i].get(), ii=i: self.setParameters(ii,v,c) )
            self.valVar[ch][i].trace("w", lambda name, index, mode, c=ch, ii=i: self.changeParameter(ii,c) )
            
             
                 
            
            tk.Label(frm,text=prop['name']).grid(row=i,column=0)
            tk.Entry(frm,textvariable=self.valVar[ch][i], justify=tk.RIGHT, 
                         # validate='all', validatecommand=(self.floatValidator, '%P')
                    ).grid(row=i,column=1)
            tk.Label(frm,text=prop['unit']).grid(row=i,column=2)
            tk.Scale(frm, variable=self.valVar[ch][i], 
                         from_=prop['min'], to=prop['max'], resolution=prop['step'],
                         digits=10 if prop['type']=="float" else 0 ,
                         showvalue=False, length=200, orient='horizontal'
                    ).grid(row=i,column=3)
            #createControl()
            
        #             par.strValue.trace("w", lambda name, index, mode, par=par: self.changeSignalParams(channel,par))

    
    def readModeConfiguration(self):
        """ read modes from slave for both channels and setting up widget accordingly """
        
        logger.debug("Reading mode configurations")     
        for ch in range(NO_OF_CHANNELS):
            cid = ch+1
            logger.debug(f"Reading for channel {ch}")     
            self.sigModeOptionMenu[ch]['menu'].delete(0, "end") # delete widtget content
            modes = [ m['name'] for m in self.getModesProperties(cid)]
            if len(modes)<1: 
                self.addStatusLine(f"failed to read modes for channel {cid}, try to re-connect (modes: {modes}","red")
                continue # if no modes, just sci
            for i,mode in enumerate(modes):
                logger.debug(f"Mode {i} of channel {cid}: {mode}")
                self.sigModeOptionMenu[ch]['menu'].add_command(label=mode, command=lambda ch=ch, i=i,modes=modes: self.setOutputMode(i,ch,modes) )                
            
            logger.debug("Copying mode from slave")     
            mode = self.getMode(cid)
            self.outputMode[ch].set(modes[mode]) # set widget
            self.readParameterConfiguration(ch)
            
        #logger.debug("----  done -------")     

        #self.outputMode[cid].trace("w", lambda  name, index, mode, channel=channel, v=self.outputMode[cid]: self.changeOutputMode(channel, v ) )
        #sigMode = tk.OptionMenu(frame, self.outputMode[cid], *self.outputModes )
        # "w", lambda  name, index, mode, channel=channel, v=self.outputMode[cid]: self.changeOutputMode(channel, v ) 
 
    
    def createControlFrame(self,channel,parent):
        """ create a frame with all the controls
            consiting of signal type selector, mode 
            selector and modifier selector
        """
        
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        frame.pack(side=tk.LEFT,fill=tk.BOTH)


        cid = channel-1
        self.modeParameterFrame[cid] = tk.Frame(frame, relief=tk.RAISED, borderwidth=1)
        self.modeParameterFrame[cid].pack(side=tk.BOTTOM, fill=tk.BOTH)
        #self.modeParameterFrame[cid].pack(side=tk.BOTTOM, fill="x")
                        
               
        # signal type selection 
        #self.signaltype[cid].trace("w", lambda  name, index, mode, channel=channel, nbook=self.tabControl[cid], v=self.signaltype[cid]: self.changeSignalMode(channel, nbook, v ) )
        #self.signaltype[cid].set(sigs[0])
        #sigType = tk.OptionMenu(frame, self.signaltype[cid], *sigs)
        #sigType.config(width=12)
        #sigType.pack(side=tk.LEFT)

        # output mode selection 
        self.sigModeOptionMenu[cid] = tk.OptionMenu(frame, self.outputMode[cid],[])
        self.sigModeOptionMenu[cid].config(width=12)
        self.sigModeOptionMenu[cid].pack(side=tk.LEFT, expand=True)
            
        #tk.Button(frame,text="CheckA",command=self.myCheck).pack()


    def myCheck(self):
        print("mycheck")
        a = self.queryCommand("!A")
        print("result: " + str(a))
        

    def addStatusLine(self,x,color="black"):
        Thread(target=self.addStatusLine_int,args=(x,color,),name=f"statusLineAdder({x})").start()
        
    def addStatusLine_int(self,x,color="black"):
        if len(x)>1 and x[-1] != "\n": x+= "\n"
        
        with self.data_lock:
            lineCount = int(self.statusText.index('end-1c').split('.')[0])
            self.statusText.insert(tk.END, x)    

        tag = "Line"+str(lineCount)
        self.statusText.tag_add(tag, str(lineCount)+".0", str(lineCount)+".9999")
        self.statusText.tag_config(tag, foreground=color)
        self.statusText.see(tk.END)        
        

        
    def getHistoryCommand(self,x,y):
        if len(self.commandHistory) == 0: return 
        self.commandString.set(self.commandHistory[ self.commandHistoryID -1] ) 
        self.commandHistoryID = max(0,self.commandHistoryID - 1)

    
    def createStatusTextFrame(self,parent):
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        frame.pack(side=tk.BOTTOM,fill=tk.BOTH)

        #self.command = tk.Text(frame, height=1, textvariable=self.commandString).pack(side=tk.BOTTOM, expand=True, fill='both')
        self.commandEntry = tk.Entry(frame, textvariable=self.commandString )        
        self.commandEntry.pack(side=tk.BOTTOM, expand=True, fill='x')
        self.commandEntry.bind('<Return>', lambda x,y=self.commandString: self.sendCommandFromGUI(x,y))
        self.commandEntry.bind('<Up>', lambda x,y=self.commandString: self.getHistoryCommand(x,y))


        self.statusText = tk.Text(frame, height=16)
        self.statusText.delete("1.0",tk.END)
        self.statusText.pack(side=tk.LEFT, expand=True, fill='both')
        scroll = tk.Scrollbar(frame)
        scroll.config(command=self.statusText.yview)
        self.statusText.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        
        def ctrlEvent(event):
            if(12==event.state and event.keysym=='c' ):
                return
            else: return "break"

        self.statusText.bind("<Key>", lambda e: ctrlEvent(e))


    
    def sendCommand(self,cmd):
        logger.error("HERE!!!!")
        if cmd=="?": 
            logger.info(self.getUnhandledResponces())
            return None
        else:
            logger.info(f"Sent >{cmd}< to device")
            ret = self.queryCommand(cmd)
            logger.info(f" ... return {ret}")        
            self.addStatusLine( "S: " + str(cmd) +"\n" )
            self.addStatusLine( "R: " + str(ret) +"\n")
        return ret
    
        
    def sendCommandFromGUI(self,event,cmd):
        com = cmd.get()
        cmd.set("")
        self.commandHistory.append(com)        
        self.commandHistoryID = len(self.commandHistory)
        
        print("UNHANDLED: " , self.getUnhandledResponces() ) 
        return self.sendCommand(com)
        

    def updateConnectionMenu(self):        
        self.connectMenu.delete( 3, tk.END ) 
        for c in range(MAX_LAST_CONNECTION_ENTRIES):            
            if( (conf := cfg.readStr("connections",f"last{c}")) not in [None,''] ) :
                self.connectMenu.add_command(label=conf, command=partial(self.menuConnectSerial,conf))
        
    def createMenu(self):        
        menubar = tk.Menu(self.main)
        self.main.config(menu=menubar)

        self.connectMenu = tk.Menu(menubar, tearoff=0)
        self.connectMenu.add_command(label="Serial", command=self.serialDialog)
        self.connectMenu.add_command(label="Ethernet", command=self.ethernetDialog)
        self.connectMenu.add_separator()
        self.updateConnectionMenu()
        menubar.add_cascade(label="Connect", menu=self.connectMenu)

        miscMenu = tk.Menu(menubar, tearoff=0)
        miscMenu.add_command(label="Configure Device", command=self.showConfigArea)
        miscMenu.add_separator()
        miscMenu.add_command(label="Help", command=donothing)
        miscMenu.add_command(label="Version", command=donothing)
        menubar.add_cascade(label="Misc", menu=miscMenu)
        
    def runGUI(self):
        
        self.running = True;
        #self.main.after(100, self.update_status) 
        self.main.mainloop()
        
    def update_status(self):
        
        if not self.running: return
     
        if not self.isConnected(): self.setDisConnected()
        
        #if self.isConnected(): self.window['connect_status'].update('connected',button_color=('white', 'green'))
        #else:self.window['connect_status'].update('not connected',button_color=('white', 'red'))

        self.main.after(100, self.update_status) 
    
    



#def handle_keypress(event):
  #  """Print the character associated to the key pressed"""
  #  print(event.char)
   # if (event.char=='x'): window.destroy()
#window.bind("<Key>", handle_keypress) # Bind keypress event to handle_keypress()


def main():
  
    try:
        logger.info("Initializing and creating GUI")
        gui= FcnGenGUI()
        logger.info("Creating initial GUI")
        gui.create()
        logger.info("Running GUI")
        gui.runGUI()        
        logger.info("GUI stopped")
    except Exception as e:
        logger.error("GUI terminated: " + str(e))
        logger.exception(e)
    finally:
        try:
            if gui: gui.close()
            logger.info("GUI closed")
        except Exception as e:
            logger.error("Could not close gui")
            logger.exception(e)
        finally:
            logger.info("program terminated")
    


    
if __name__ == '__main__':
    
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    import builtins; builtins.print = partial(print, flush=True)

    #graphviz = GraphvizOutput()
    #graphviz.output_file = 'basic.png'
    #with PyCallGraph(output=graphviz):

    t = countThreads(); logger.info(f"Threads before : {t}")
    printAllThreads()
    
    main()

    t=countThreads();logger.info(f"Threads after closing: {t}")
    printAllThreads()
    
