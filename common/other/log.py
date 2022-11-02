from datetime import datetime
import logging, os, shutil
from pprint import pprint


class Log_Manage():
    '''
    This class is to Manage logfiles.
    author: Kail
    '''
    def __init__(self, logger=''):
        '''
        description: init the class vars
        author: Kail
        params: logger, the logfile
        '''
        self.logger = logger if logger else Logger(log_file='log_manage')

    def clear_log(self, logdir, assumeyes=None):
        '''
        description: clear or keep logs in logdir
        author: Kail
        params: logdir, the log path, type str
                assumeyes     ['y', 'Y', 'n', 'N']
                    y and Y is delete file in logdir
                    n and N is keep file in logdir
        return: nodir, logdir not exist
        '''
        if not os.path.isdir(logdir):
            self.logger.error('%s is not a folder')
            return 'nodir'
        if logdir.startswith('.'):
            logdir = os.path.realpath(os.path.join(os.getcwd(), logdir))
        logfiles = [
            os.path.join(path, f) for path, dirs, files in os.walk(logdir) for f in files if not f.endswith('.initial')
        ]
        log_num = len(logfiles)
        if log_num != 0:
            if not assumeyes:
                print('    ' + '\n    '.join(logfiles))
                while True:
                    ans = input('WARNING: Continue to remove above files\n    ' +
                                'Please input [y/n](y is delete, n and Enter key is no)? ')
                    if ans in ['Y', 'y']:
                        self.logger.debug('assumeyes: ' + str(ans))
                        assumeyes = 'y'
                        break
                    elif ans in ['n', 'N', '']:
                        self.logger.debug('assumeyes: ' + str(ans))
                        assumeyes = 'n'
                        break
                    else:
                        print('Error: Illegal input')
            if assumeyes in ['y', 'Y']:
                for e in logfiles:
                    self.logger.info(' ---> remove the log {0}'.format(e))
                    # os.remove(e)
                shutil.rmtree(logdir)
                os.makedirs(logdir)


class Logger():
    '''
    logging module for TEA. Encapsulated python logging module.
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        self.log_file = kwargs.get('log_file')
        self.stdoutput = kwargs.get('stdoutput', True)
        self.log_file_timestamp = kwargs.get('log_file_timestamp', True)
        self.log_level = kwargs.get('log_level', 'DEBUG').upper()
        self.log_formatter = kwargs.get('log_formatter', '%(asctime)s %(levelname)s: %(message)s')

        if self.log_file and 'name' not in kwargs:
            self.name = self.log_file #logger's name
        else:
            self.name = kwargs.get('name', 'TEA')

        self.logger = logging.getLogger(self.name)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        # formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s') 
        formatter = logging.Formatter(self.log_formatter) 

        LEVEL = {
                    "ERROR" : logging.ERROR,
                    "WARNING" : logging.WARNING,
                    "INFO" : logging.INFO,
                    "DEBUG" : logging.DEBUG,
                    "CRITICAL" : logging.CRITICAL,
                } 
        
        self.logger.setLevel(LEVEL[self.log_level])

        #set console output:
        console_output = False

        #check if screen output is set:
        for hd in self.logger.handlers:
            if not isinstance(hd, logging.FileHandler) and isinstance(hd, logging.StreamHandler):
                console_output = True
                break

        if self.stdoutput and not console_output:
            console = logging.StreamHandler()
            console.setLevel(LEVEL[self.log_level])
            console.setFormatter(formatter)
            self.logger.addHandler(console)
    
        #set log file:
        if self.log_file:  
            if self.log_file_timestamp:
                self.log_file = self.log_file + '_' + timestamp + ".log"

            fh = logging.FileHandler(self.log_file)                
            fh.setLevel(LEVEL[self.log_level])
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
    
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
        
    def info(self, msg, *args, **kwargs):        
        self.logger.info(msg, *args, **kwargs)  
    
    def warn(self, msg, *args, **kwargs):        
        self.logger.warning(msg, *args, **kwargs) 
            
    def error(self, msg, *args, **kwargs):        
        self.logger.error(msg, *args, **kwargs)   
        
    def critical(self, msg, *args, **kwargs):        
        self.logger.critical(msg, *args, **kwargs) 
