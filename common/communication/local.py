import subprocess
import re
from common.communication.session import Session

class Local(Session):
    '''
    this class is used for local cmd interface.
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        '''
        description: __init__ for Local class
        author: houyuhan
        params: kwargs, options need to customized to the session
                encoding: UTF-8(default), for windows: ANSI
                shell: True or False
                On Windows with shell=True, the COMSPEC environment variable specifies 
                the default shell. The only time you need to specify shell=True on Windows is when the command 
                you wish to execute is built into the shell (e.g. dir or copy). You do not need shell=True to 
                run a batch file or console-based executable.

        return: cmd result        
        '''
        Session.__init__(self, **kwargs)
        self.encoding = kwargs.get('encoding', 'UTF-8')
        self.shell = kwargs.get('shell', True)


    def cmd(self, cmd_line, **kwargs):
        '''
        description: send cmd and get return
        author: houyuhan
        params: cmd_line, the cmd line need to send to the remote system
                kwargs, options need to customized to the session
                      return_list: True(default) or False cmd result into list by lines or not     
                shell: True or False
                On Windows with shell=True, the COMSPEC environment variable specifies 
                the default shell. The only time you need to specify shell=True on Windows is when the command 
                you wish to execute is built into the shell (e.g. dir or copy). You do not need shell=True to 
                run a batch file or console-based executable.                               
        return: cmd result
        
        '''    
        output = ''
        return_list = kwargs.get('return_list', True)
        shell = kwargs.get('shell', self.shell)

        self.logger.info('running command:\n' + cmd_line)

        try:
            output = subprocess.check_output(cmd_line, stderr=subprocess.STDOUT, shell=shell)
            output = output.decode(encoding=self.encoding)

        except subprocess.CalledProcessError as e:
            output = e.output
            output = output.decode(encoding=self.encoding)
        
        output = output.strip()

        self.logger.info(output)
        if return_list:
            output = [l.strip() for l in re.split('[\r\n]+', output)]
             
        return output


    def bk_cmd(self, cmdline, **kwargs):
        '''
        description: run cmd in a new process, the process could be closed if the python program is interrupted.
        author: houyuhan
        params: cmd_line, the cmd line need to send to the remote system
                kwargs, options need to customized to subprocess.popen
                                              
        return: Popen object
        '''     

        self.logger.info('running command in background:\n' + cmdline)
        return subprocess.Popen(cmdline, shell=True, **kwargs) 
    
    

    def close(self):
        pass


