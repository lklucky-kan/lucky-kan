import os
from datetime import datetime
from common.other.log import Logger

class Hardware():
    '''
    decription: this class is the parent class for all hardware related classes
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        '''
        description: init method of this class
        author: yuhanhou
        params: kwargs, optional keyword param
                        ip, 
                        user,
                        password,
                        protocol, remote connection protocol
                        port, protocol related port, like ssh is 22
                        logger, logger object, default is using log file with the ip address and timestemp
        '''

        self.ip = kwargs.get('ip', 'localhost')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.protocol = kwargs.get('protocol')
        self.port = kwargs.get('port')
        self.log_path = kwargs.get('log_path', '')
        self.hw_type = kwargs.get('hw_type', '') #server, bmc, pdu, storage, switch, etc...
        self.options = kwargs
        #create logger
        if kwargs.get('logger'):
            self.logger = kwargs.get('logger')
        else:
            # timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file = kwargs.get('log_file', self.ip)

            if self.log_path != '':
                log_file = os.path.join(self.log_path, self.ip)

            log_opts = {
                'log_file':log_file,
                'stdoutput':False,
            }

            if kwargs.get('log_formatter'):
                log_opts['log_formatter'] = kwargs.get('log_formatter')
                
            self.logger = Logger(**log_opts)