import re
from common.infrastructure.hardware import Hardware
from common.communication.ipmi import IPMI
from common.communication.redfish import Redfish


class BMC(Hardware):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = kwargs.get('user', 'admin')
        self.password = kwargs.get('password', 'admin')
        self.protocol = kwargs.get('protocol', 'ipmi')

        session_opts = kwargs.copy()
        session_opts.update(user=self.user, password=self.password, logger=self.logger)

        if re.search('ipmi', self.protocol, re.I):
            self.session = IPMI(**session_opts)
        elif re.search('redfish', self.protocol, re.I):
            self.session = Redfish(**session_opts)
            pass

    def cmd(self, cmdline, **kwargs):
        '''
        description: this is a wrapper of session cmd method
        author: yuhanhou
        params: please refer to the session's cmd or request options
        '''
        return self.session.cmd(cmdline, **kwargs)




    