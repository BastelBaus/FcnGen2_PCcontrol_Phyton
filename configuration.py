# -*- coding: utf-8 -*-
"""
Created on Mon May 16 19:52:35 2022

@author: pagan
"""

import configparser
import io
import os


import my_logger
logger = my_logger.get_logger(__name__)


configfile_name = "config.yaml"
logger.info("Configuration Filename:" + str ( configfile_name ))



# Check if there is already a configurtion file
if not os.path.isfile(configfile_name):

    logger.info("There was no file, creating initial file")
    # Add content to the file
    Config = configparser.ConfigParser()
    Config.add_section('favcon1')
    Config.set('favcon1', 'IP', 'None')
    Config.set('favcon1', 'PORT', 'COM12')
    Config.set('favcon1', 'baudrate', '115200')
    Config.add_section('other')
    #Config.set('other',
    #           'preprocessing_queue',
    #           ['preprocessing.scale_and_center',
    #            'preprocessing.dot_reduction',
    #            'preprocessing.connect_lines'])
    #Config.set('other', 'use_anonymous', True)

    # Create the configuration file as it doesn't exist yet
    cfgfile = open(configfile_name, 'w')
    Config.write(cfgfile)
    cfgfile.close()
   

logger.info("Loading configuration file")
Config = configparser.ConfigParser()
Config.read(configfile_name);
    

def readFloat(section,option):
    try: 
        logger.debug(f"read float @{section} option:{option}")
        return float(Config.get(section,option))
    except Exception as e:
        logger.warning(str(e))
        return None

def readStr(section,option):
    try: 
        logger.debug(f"read str @{section} option:{option}")
        s = str(Config.get(section,option))
        if s=='None': return None
        else: return s
    except Exception as e:
        logger.warning(str(e))
        return None

def writeStr(section,option,value):
    try: 
        logger.debug(f"write @{section} option:{option} = {value}")
        if not Config.has_section(section): Config.add_section(section)
        Config[section] = {option:value}
        
        cfgfile = open(configfile_name, 'w')
        Config.write(cfgfile)
    except Exception as e:
        logger.warning(str(e))
    finally:
        if 'cfgfile' in locals(): cfgfile.close()

def pushStr(section,option,value,maxItems = 6):
    try: 
        logger.debug(f"push @{section} option:{option} = {value} (maxItems:{maxItems})")
        if not Config.has_section(section): Config.add_section(section)
        
        opt = [ str(value) ];
        for i in range(maxItems-1): 
           opt.append( Config[section].get(str(option + str(i))) if not '' else None )
        opt = list(dict.fromkeys(opt))
        del opt[maxItems:-1]
        opt.extend( [None]* (maxItems-len(opt)) ) 
        
        for i,val in enumerate(opt): 
            if val is None: Config.set(section, str(option + str(i)),"")
            else:           Config.set(section, str(option + str(i)),opt[i])
        
        cfgfile = open(configfile_name, 'w')
        Config.write(cfgfile)
    except Exception as e:
        logger.warning(str(e))
    finally:
        if 'cfgfile' in locals(): cfgfile.close()


        