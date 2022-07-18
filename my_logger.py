
# app_logger.py
import logging



#_log_format = f"%(asctime)s - [%(levelname)s] - %(name)-30s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
_log_format = f"[%(levelname)-7s] %(name)-20s : %(message)s"

_file_log_format = f"%(asctime)s [%(levelname)-7s] : %(message)s"

LogFiles = ["FunctionGeneratorGUI","__main__"]


handler = logging.StreamHandler()
handler.terminator = ""


# ToDO: nbring colors into play
# https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output


class ModuleLogFilter(logging.Filter):

    def filter(self, record):      
        res = (record.module in LogFiles) or (record.levelno > logging.DEBUG )
        #print("---------------> ",record.module ," in ", LogFiles, " = ",res )
        return res
    
# toDo: delete all loogfiles
    

def get_file_handler(name):
    file_handler = logging.FileHandler(f"{name}.log")
    file_handler.setFormatter(logging.Formatter(_file_log_format))
    return file_handler

def get_stream_handler():
    stream_handler = logging.StreamHandler()
    #stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler

def get_logger(name):
     
    if get_logger.first: 
        logging.getLogger().handlers.clear(); 
        get_logger.first = False;
    
    logger = logging.getLogger(name)    

    if not logger.hasHandlers():
        logger.addHandler(get_stream_handler())    
        logger.setLevel(logging.DEBUG)
        logger.addFilter( ModuleLogFilter() )

    logger.info(f"Created logger to log {name}")
    return logger

get_logger.first  = True

    
def get_fileLogger(name):
    logger = logging.getLogger("file_" + name)  
    logger.addHandler(get_file_handler(name))    
    logger.setLevel(logging.DEBUG)
    logger.info(f"Created logger to log to file: {name}.log")
    return logger
    


#logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)
#logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)

logger = get_logger(__name__)
logger.info("Logger Factory set up")        

