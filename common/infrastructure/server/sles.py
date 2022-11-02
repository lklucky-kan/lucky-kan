from common.infrastructure.server.linux import Linux

class SLES(Linux):
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