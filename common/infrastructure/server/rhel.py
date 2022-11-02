import os, sys
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
    )
)
from common.infrastructure.server.linux import Linux

class RHEL(Linux):
    '''
    description: RHEL class for rhel OS operation
    author:yuhanhou   
    '''
    
    def __init__(self, **kwargs):
        '''
        description: this is a init method for OS
        author: yuhanhou
        params: kwargs, optional keyword param
                        ip, 
                        user,
                        password,
                        protocol, remote connection protocol,supported is ssh, local, telnet, winrm
                        port, protocol related port, like ssh is 22
                        logger, logger object, optional, default is using log file with the ip address and timestemp
        '''

        Linux.__init__(self, **kwargs)
