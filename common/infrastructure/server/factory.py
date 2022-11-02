import re
import platform
import os, sys
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
    )
)
sys.path.append(tea_path)
from common.infrastructure.server.rhel import RHEL
if platform.system() == 'Windows':
    from common.infrastructure.server.windows import Windows
from common.infrastructure.server.linux import Linux
from common.infrastructure.server.rhel import RHEL
from common.infrastructure.server.sles import SLES
from common.infrastructure.server.ubantu import Ubantu


class ServerFactory():
    '''
    d日4eription: this class is used for create server object
    author: yuhanhou
    ''' 

    @staticmethod
    def create_server_obj(**kwargs):
        '''
        description: create server object 
        author: yuhanhou
        params: kwargs, optional keyword param
                        os, os type like windows, rhel, linux, centos, etc
                        ip, os ip
                        user, os user
                        password, os password
                        protocol, remote connection protocol,supported is ssh, local
                        port, protocol related port, like ssh is 22
                        logger, logger object, optional, default is using log file with the ip address and timestemp
        '''    
        #if no OS is defined will create the current OS running the code:
        if 'os' not in kwargs or re.search('current|localhost',kwargs.get('os'), re.I):
            os_name = platform.platform()
            kwargs.update(os=os_name)

        if re.search('linux|centOS', kwargs.get('os'), re.I):
            return Linux(**kwargs)
        elif re.search('rhel|redhat', kwargs.get('os'), re.I):
            return RHEL(**kwargs)
        elif re.search('sles|suse', kwargs.get('os'), re.I):
            return SLES(**kwargs)
        if re.search('ubantu', kwargs.get('os'), re.I):
            return Ubantu(**kwargs)
        elif re.search('win', kwargs.get('os'), re.I):
            return Windows(**kwargs)


