from common.communication.session import Session
from common.communication.local import Local


class IPMI(Session):
    '''
    description: This is a ipmitool class to support ipmitool connection
    author: zhuangzhao
    '''

    def __init__(self, **kwargs):
        Session.__init__(self, **kwargs)
        self.cipher = 17

    def cmd(self, cmd_line, **kwargs):
        '''
        description: send cmd and get return
        author: zhuangzhao
        params: cmd_line, The ipmitool command of the BMC needs to be sent
                kwargs, options need to customized to the session
                      Required parameters is  parameters of the BMC(e.g. ip =bmc_ip ..)
        return: cmd result
        '''
        cmd_list = [
            f'ipmitool -I lanplus',
            f'-H {self.ip}',
            f'-U {self.user}',
            f'-P {self.password}',
            f'-C {self.cipher}',
            cmd_line
        ]
        cmd_text = ' '.join(cmd_list)
        local = Local()
        result = local.cmd(cmd_text, **kwargs)
        return result
