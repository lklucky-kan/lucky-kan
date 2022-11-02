import winrm
import re
from common.communication.session import Session

class Winrm(Session):
    '''
    run cmd as Adminstrator,
    winrm quickconfig -force
    windows system need to be performed with below commands
    winrm set winrm/config/client/auth @{Basic="true"}
    winrm set winrm/config/service/auth @{Basic="true"}
    winrm set winrm/config/service @{AllowUnencrypted="true"}
    
    *need to deploy error handling, like while the session is not active, need to re-establish the session

    1. winrm.exceptions.InvalidCredentialsError: the specified credentials were rejected by the server
    
    !!!need bebug this moudle before use.
    
    '''    

    def __init__(self, key_file=None, **session_attr):
        Session.__init__(self, **session_attr)
        self.client = None
        
        self.open = False
        self.open_session()

    def open_session(self):
        self.open = True
        self.client = winrm.Session(self.ip, auth=(self.user, self.passwd))

    def cmd(self, cmd_line, return_list=1, **kwargs):
        self.logger.info("sending command: " + cmd_line)
        if not self.open:
            raise ValueError("winrm tunnel not open.")
        r = self.client.run_cmd(cmd_line)
        
        outstr = r.std_out
        errstr = r.std_err
        if errstr:
            outstr = outstr + errstr
        self.logger.debug("status_code: " + str(r.status_code))

        self.logger.info("get reply: \n" + outstr)
        if return_list:
            return re.split(r'[\r\n]+', outstr)
        return outstr
    
    def pshell(self, cmd_line, need_arr = 1):
        self.logger.info("sending command: " + cmd_line)
        if not self.open:
            raise ValueError("winrm tunnel not open.")
        r = self.client.run_ps(cmd_line)
        outstr = r.std_out
        errstr = r.std_err
        if errstr:
            outstr = outstr + errstr
        
        self.logger.debug("status_code: " + str(r.status_code))

        self.logger.info("get reply: \n" + outstr)
        if need_arr:
            return re.split(r'[\r\n]+', outstr)
        return outstr

    def close(self):
        self.open = False
        self.client = None