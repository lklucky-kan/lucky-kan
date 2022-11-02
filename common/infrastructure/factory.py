import re
from common.infrastructure.server.factory import ServerFactory
from common.infrastructure.sm.bmc import BMC
from common.infrastructure.dm.pdu import PDU


class HardwareFactory():
    '''
    description: this class is used for create hw object
    author: yuhanhou
    ''' 

    @staticmethod
    def create_hw_obj(**kwargs):
        '''
        description: create hw object 
        author: yuhanhou
        params: kwargs, optional keyword param include all the required keyword values to create the hardware object
                    and hw_type is required for this method:
                    hw_type: server|bmc|pdu|...
        return: object created for the hardware               
        '''    
        hw_type = kwargs.get('hw_type', '')
        if re.search('server', hw_type, re.I):
            return ServerFactory.create_server_obj(**kwargs)
        elif re.search('bmc', hw_type, re.I):
            #please add a sub factory module for bmc if more type bmc is used in the testing!
            #just refer to the ServerFactory.py
            #currectly, we use BMC class only
            return BMC(**kwargs)
        elif re.search('pdu', hw_type, re.I):
            #please add a sub factory module for bmc if more type PDUs is used in the testing!
            #just refer to the ServerFactory.py
            #currectly, we use PDU class only which actually is APC PDU     
            return PDU(**kwargs)
        else:
            pass
            #please extend more hw types creating here