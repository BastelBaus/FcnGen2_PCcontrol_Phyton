# -*- coding: utf-8 -*-
"""
Created on Mon May  9 19:47:31 2022

@author: pagan
"""


from pynput.keyboard import Key, Listener
import PySimpleGUI as sg
from tkinter import ttk
import threading
import time
import logging
from FcnGen import FcnGen
import math
from PIL import Image
import serial.tools.list_ports

import configuration as cfg


logger = logging.getLogger('FcnGenGUI')     

def checkSlave(window):
    global RUNNING
    while RUNNING:
        window.write_event_value("-CHECKSLAVE-",("Test",None))
        time.sleep(1)


class mySin:
    def __init__(self,A,b,f,p=0):
        self.A = A; self.b=b; self.f=f; self.p=p;
        
    def __call__(self,x):
        return math.sin(2*math.pi*self.f*x+self.p)*self.A + self.b

class myPulse:
    def __init__(self,A,b,f,p=0):
        self.A = A; self.b=b; self.f=f; self.p=p;
        
    def __call__(self,x):
        
        return (((self.f * x*2 + self.p) % 2 ) > 1) * self.A + self.b
                

def makeKey(ctrl,key,name,opt=None):
    return "control:" + str(ctrl) + ':' + str(key) +':' + str(name) + (":"+str(opt) if opt else "")
def getKeyValues(key):
    values = key.split(':')
    if   len(values) == 5: return values[1:] 
    elif len(values) == 3: return values[1:] + [None]
    else: return None
    
 
from dataclasses import dataclass

@dataclass
class Value:
    channel: int = 1
    name: str = ""
    unit: str = ""
    limits: tuple = None
    IF_name: str = None
    #guiElement: object = None

    #def getKeyString(self):
    def __hash__(self):
        return hash(repr(self))
#         return hash(tuple([self.channel,self.name,self.unit, self.IF_name]))
    
    
def makeLinkedValue(channel,name,unit,limits, IF_name):
    slider = Value(channel,name,unit,limits,IF_name)
    value  = Value(channel,name,unit,limits, IF_name)
    slider.linkedValue = value
    #value.linkedValue  = slider
    return (slider, value)

#ch1_A_slider = Value(1,"A","V",(-30,30))
#ch1_A_value = Value(1,"A","V",(-30,30))
#ch1_A_slider.linkedValue = ch1_A_value
#ch1_A_value.linkedValue = ch1_A_slider
 
    
class FcnGenGUI(FcnGen):
        
    
    def __init__(self):
        self.running = False 
        self.popwindow = None
        super().__init__()
        
    def isRunning(self): return self.running

    
    def setParam(self,channel,attribute,value):
        logger.debug("Set @channel:" + str(channel) + " " + str(attribute) + " := " + str(value))
        self.setParameter(attribute,value)
        
        
    def start(self):
        logger.info("Setting up window")
        sg.theme('SystemDefault')   

        
        favs = []
        for k in [1,2,3,4,5,6]:
            i = cfg.readStr('favcon'+str(k),'IP')
            p = cfg.readStr('favcon'+str(k),'port')
            b = cfg.readValue('favcon'+str(k),'baudrate')
            if i is not None:
                favs.append( str(i) + ': ' + p + ':'+str(b)+"::con"+str(k))
                pass
            elif p is not None:
                favs.append( str(k) + ': ' + p + '@'+str(b)+"::con"+str(k))
            else:
                # no favorite
                pass
                
        cons = ['&Serial', '&Ethernet', '----------']
        cons.extend(favs)
        menu_def= ['&File', ['&New File', '&Open...','Open &Module','---', '!&Recent Files','C&lose']],['&Save',['&Save File', 'Save &As','Save &Copy'  ]],['&Connect', cons]
    
        #txt = [[sg.T('A New Input Line'),sg.T('A New Input Line 2')],[sg.T('A New Input Line'),sg.T('A New Input Line 2')],[sg.T('A New Input Line'),sg.T('A New Input Line 2')],[sg.T('A New Input Line'),sg.T('A New Input Line 2')],[sg.T('A New Input Line'),sg.T('A New Input Line 2')]]
        
        def opElement(element,key):
            #return [[sg.pin(sg.Column('', [[element]] ,key=key))]]
            #return sg.Frame('', [[element]] ,key=key)
            #return [[sg.Frame('', [[element]] ,key=key,visible=False)]]
            return [[sg.pin(sg.Frame('', [[element]] ,key=key,visible=False,pad=(0,0)))]]
        
            
        def makeKey(ctrl,key,name,opt=None):
            return "control:" + str(key) +':'+ str(name) + (":"+str(opt) if opt else "")
        def getKeyValues(key):
            values = key.split(':')
            if   len(values) == 4: return values 
            elif len(values) == 3: return values + [None]
            else: return None
            
        def makeControl(channel,element,linkedValue):
            
            
            el = [    sg.Text(linkedValue[0].name+' = '),
                      sg.InputText('0.0',justification='right',enable_events = True,key=linkedValue[0],size=(10,None),pad=(0,None)),
                      sg.Text(linkedValue[0].unit),
                      sg.Slider(orientation ='horizontal', key=linkedValue[1], range=(linkedValue[1].limits[0],linkedValue[1].limits[1]),enable_events = True)
                      #sg.Slider(orientation ='horizontal', key=lambda x: self.setParam(channel,IF_name,x), range=(1000,10000),enable_events = True)
                      
                 ]
            return el

        def makeControl2(channel,element,name,unit='',IF_name=None):
            
            key = str(channel)+":"+element
            controlKey = makeKey("value",key,name)
            sliderKey = makeKey("slider",key,name)
            
            el = [    sg.Text(name+' = '),
                      sg.InputText('0.0',justification='right',enable_events = True,key=controlKey,size=(10,None),pad=(0,None)),
                      sg.Text(unit),
                      #sg.Slider(orientation ='horizontal', key=sliderKey, range=(1000,1000000),enable_events = True)
                      sg.Slider(orientation ='horizontal', key=lambda x: self.setParam(channel,IF_name,x), range=(0,255),enable_events = True, disable_number_display=True)
                      
                 ]
            return el

        def makeControlPanel(channel,element,linkedValueList):
            eList = []
            for a in linkedValueList:
                eList.append( makeControl(channel,element,a ) )        
            eList.append([sg.VSeperator()])
            eList.append([sg.Image('sin.png',size=(400,217))])
            #eList = [ sg.Column(eList),sg.Column( [[sg.Image('sin_400_217.png',size=(400,217))]]) ]
            tabKey = str(channel)+":"+element
            return sg.Tab(tabKey,eList)

        def makeControlPanel2(channel,element,nameList):
            eList = []
            for a in nameList:
                eList.append( makeControl2(channel,element,a[0],a[1],a[2]  ) )        
            eList.append([sg.VSeperator()])
            eList.append([sg.Image('sin.png',size=(400,217))])
            #eList = [ sg.Column(eList),sg.Column( [[sg.Image('sin_400_217.png',size=(400,217))]]) ]
            tabKey = str(channel)+":"+element
            return sg.Tab(tabKey,eList)
            
        tab11 = makeControlPanel(1,'sin',    
                             [ makeLinkedValue(1,"A","V",(0,255),"amplitude"),
                               makeLinkedValue(1,"f","Hz",(0,3000000),"frequency"),
                               makeLinkedValue(1,"O","V",(0,30),"offset") 
                             ])
        tab12 = makeControlPanel(1,'square',    
                             [ makeLinkedValue(1,"A","V",(0,30),"amplitude"),
                               makeLinkedValue(1,"f","Hz",(0,3000000),"frequency"),
                               makeLinkedValue(1,"O","V",(0,30),"offset") 
                             ])
        tab13 = makeControlPanel(1,'triangle',    
                             [ makeLinkedValue(1,"A","V",(0,30),"amplitude"),
                               makeLinkedValue(1,"f","Hz",(0,3000000),"frequency"),
                               makeLinkedValue(1,"O","V",(0,30),"offset") 
                             ])
        tab14 = makeControlPanel(1,'sin-chirp',    
                             [ makeLinkedValue(1,"A","V",(0,30),"amplitude"),
                               makeLinkedValue(1,"f","Hz",(0,3000000),"frequency"),
                               makeLinkedValue(1,"O","V",(0,30),"offset") 
                             ])
                               
                        
        
        tab11 = makeControlPanel2(0,'sin',      [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab12 = makeControlPanel2(0,'square',   [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab13 = makeControlPanel2(0,'triangle', [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab14 = makeControlPanel2(0,'sin-chirp',[('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        
        tab21 = makeControlPanel2(2,'sin',      [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab22 = makeControlPanel2(2,'square',   [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab23 = makeControlPanel2(2,'triangle', [('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        tab24 = makeControlPanel2(2,'sin-chirp',[('A','V',"amplitude"),('f','Hz',"frequency"),('O','V',"offset")])
        
        tabGroup1 = [sg.TabGroup([[tab11,tab12,tab13,tab14]], enable_events=False, key='-TABGROUP1-') ]
        tabGroup2 = [sg.TabGroup([[tab21,tab22,tab23,tab24]], enable_events=False, key='-TABGROUP2-') ]
        combo1 = [  sg.Combo(['sin','square','triangle', 'sin-chirp'],default_value='sin',key='function1',enable_events = True),
                    sg.Combo(['Mode1','Mode2','Mode3', 'Mode4'],default_value='Mode1',key='mode1',enable_events = True)
                 ]
        combo2 = [sg.Combo(['sin','square','triangle', 'sin-chirp'],default_value='sin',key='function2',enable_events = True)]
        
        layout = [  
                [sg.Menu(menu_def, text_color='navy', disabled_text_color='yellow' )],    
                [   sg.Button('not connected', enable_events = True,key='connect_status'), sg.Text('COM1 @ 115200 baud',key='connection_device'),
                    sg.Button('REBOOT'),sg.Button('CHKI2C'),
                ],
                #[sg.Column([[tabGroup, sg.Image('sin.png',size=(200,200))]],vertical_alignment='t'),sg.VSeperator(),sg.Column(sg.Text('test'))],
                #[ sg.Column([[tabGroup, sg.Image('sin_400_217.png',size=(400,217))]]),
                #  sg.VSeperator(),
                #  sg.Column([[sg.Text('test')]]) ],
                [ sg.Frame("Channel 1",[combo1,tabGroup1]) , sg.Frame("Channel 2",[combo2,tabGroup2]) ],
                [sg.Button('S3'), sg.Button('S4'), sg.Button('S7'), sg.Button('S8')],
                #[sg.Text('PWM (ofs): '),sg.Slider(orientation ='horizontal', key='PWM', range=(0,2048-1),enable_events = True)],    
                #[sg.Text('Frequency: '),sg.Slider(orientation ='horizontal', key='FREQ', range=(1000,1000000),enable_events = True)],    
                #[sg.Text('GAin: '),sg.Slider(orientation ='horizontal', key='GAIN', range=(0,255),enable_events = True)]    ,
                #[sg.Column(txt, scrollable=True, background_color="white", vertical_scroll_only=True, expand_x=True, key='-COL1-')]
                #[sg.Column(txt, scrollable=True, background_color="white", vertical_scroll_only=True, expand_x=True, key='-COL1-')]
                  [ sg.Multiline('',size = (None, 12), autoscroll=True, key='-COL1-')]
                ]
        
        nada = ( 0, 0, 0, 0 )  
        self.window = sg.Window('FcnGen', layout, finalize=True, margins = nada)
        
        style = ttk.Style()
        style.layout('TNotebook.Tab', [])                           # Hide tab bar
        self.window['-TABGROUP1-'].Widget.configure(width=300, height=220) # Set size
        self.window['-TABGROUP2-'].Widget.configure(width=300, height=220) # Set size

        #readData = threading.Thread(target=checkSlave, args=(self.window,), daemon=True)

        self.window.bring_to_front()
        self.window.keep_on_top_clear()
        self.running = True; 

    
    def loop(self):
        self.handle_input()
        self.update_status()

    def handle_input(self):
    
        if self.popwindow is not None: event, values = self.popwindow.read(timeout = 0.1)
        else: event, values = self.window.read(timeout = 0.1)
    
        
        if event == "__TIMEOUT__": return
        logger.debug('\n\nEvent: >%s< values: %s' %(event,values))


        if callable(event):
            logger.debug('Calling Event: ' + str(event))
            logger.debug('values: ' + str(values[event]))            
            event(values[event]);
            return


        if event is not sg.WIN_CLOSED: event = event.split("::")[1] if "::" in event else event


        if self.popwindow is None and ( event == sg.WIN_CLOSED or event == 'Cancel' ) : # if user closes window or clicks cancel
            self.disconnect()
            self.window.close()
            self.running = False; 
        elif event == "REBOOT":
            self.addLine("Sending reboot command to slave")
            self.addLine("Connected: %d " % self.isConnected())
            self.sendCommand('x')
            
        elif event == 'CHKI2C':
            self.addLine("Checking I2C")
            self.sendCommand('y')
            
        elif event == 'Popup_Cancel':
            self.popwindow.close()
            self.popwindow = None
        elif event == 'Popup_Connect':
            self.popwindow.close()
            self.popwindow = None
            self.window['connection_device'].update( values['COMport'] + ' @ ' + values['COMbaudrate'] )
            self.connect(port=values['COMport'],baudrate=int(values['COMbaudrate']))
            self.addLine("Connecting to serial interface: " + values['COMport'] + ' @ ' + values['COMbaudrate'])
            logger.debug('Connection done')
        elif event == 'con1' or event == 'con2' or event == 'con3' or event == 'con4' or event == 'con5' or event == 'con6' :
            k = event[3]
            i = cfg.readStr('favcon'+str(k),'IP')
            p = cfg.readStr('favcon'+str(k),'port')
            b = cfg.readValue('favcon'+str(k),'baudrate')
            print(k,i,p,b)
            if i is not None:
                print('con ethernet')
                pass
            elif p is not None:
                print('x')
                self.connect(port=p,baudrate=int(b))
            else:
                # no favorite
                pass
            
            
        elif event =="connect_status":
            if self.isConnected(): self.disconnect()
            else: self.connect()
        
        elif event == "Serial":

            availabelPorts = [a.device for a in serial.tools.list_ports.comports()]
            baudrates      = ['9600','115200']
            layout = [ [ sg.Combo(availabelPorts,default_value=availabelPorts[0],key='COMport',    enable_events = False), 
                         sg.Combo(baudrates,     default_value='115200',         key='COMbaudrate',enable_events = False),
                         sg.Button('Popup_Connect', enable_events = True),sg.Button('Cancel',key='Popup_Cancel',enable_events = True)]]
            self.popwindow = sg.Window('Connect Serial', layout, finalize=True, modal=True, margins = (0,0,0,0))
            

            #self.addLine("Connecting to serial interface")
            
        elif event == "function":
            self.window[values[event]].select()
        elif event == "mode1":
            if(    values[event] == "Mode1"): self.setMode(0,1);
            elif ( values[event] == "Mode2"): self.setMode(1,1);
            elif ( values[event] == "Mode3"): self.setMode(2,1);
            else:                             self.setMode(3,1);

     
            
        elif event == "S3": self.setConfig(3)
        elif event == "S4": self.setConfig(4)
        elif event == "S7": self.setConfig(7)
        elif event == "S8": self.setConfig(8)
        
    
    def update_status(self):
        
        if not self.running: return
        
        # reading serial data
        d = self.readData()        
        if d is not None: 
            logger.debug('Read Data: ' + str(d))
            self.addLine( d.decode() )

        # 
        if self.isConnected(): self.window['connect_status'].update('connected',button_color=('white', 'green'))
        else:self.window['connect_status'].update('not connected',button_color=('white', 'red'))
        
    def addLine(self,line):
        self.window['-COL1-'].update(line,append=True)
        pass
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    
    
    gui = FcnGenGUI()
    gui.start()
    while gui.isRunning(): 
        #gui.addLine("Add %d" % k); k = k+1
        
        gui.loop() # last command in case window is closed
    