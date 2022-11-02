import re
import shutil
import os
from common.other.log import Logger
from common.infrastructure.hardware import Hardware

class OS(Hardware):
    '''
    description: this class is the parent class for OS 
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
                        logger, logger object, default is using log file with the ip address and timestemp
        '''
        Hardware.__init__(self, **kwargs)
        self.path_sep = kwargs.get('path_sep')
        self.scripts_root_path = kwargs.get('scripts_root_path')
        self.tea_path = self.scripts_root_path + self.path_sep + 'tea'
        self.session = None
        #gen OS local log dir to put system logs:
        self.local_log_path = kwargs.get('local_log_path', '')

        if self.local_log_path == '':
            match = re.search(r'(tea\S+)', self.log_path, re.I)
            if match:
                tmp_path = match.group(1)
                tmp_path = re.sub(r'/|\\', self.path_sep, tmp_path)

                self.local_log_path = self.path_sep.join([self.scripts_root_path, tmp_path])

    
    def cmd(self, cmdline, **kwargs):
        '''
        description: this is a wrapper of session cmd method
        author: yuhanhou
        params: please refer to the session's cmd options
        '''
        return self.session.cmd(cmdline, **kwargs)
        

    def background_cmd(self, cmdline, **kwargs):
        pass


    def reboot(self, method='inband'):
        '''
        description: reboot os
        author: yuhanhou
        params: method, inband or outband
        return: NA
        '''
        pass


    def mount_smb(self, ip, share_dir, **kwargs):
        '''
        description:
        author: yuhanhou
        params: ip, smb server ip
                share_dir, shared dir of smb server
                kwargs, optional 
                    user: default is anonymous
                    password: default is ''
                    port: default is 139
        return: NA

        '''
        pass


    
    def raw_copy(self, src, des):
        '''
        description: this method is used by OS copy cmd, the src file or dir copied into des dir
        author: yuhanhou
        params: src, source file or dir
                des, target file or dir, if src is dir, des must be a dir
        return: NA
        '''
        pass


    def collect_sys_logs(self, **kwargs):
        '''
        description: collect OS system logs
        author: yuhanhou
        params: kwargs, optional kw pairs
                    des: target dir to put the collected logs
                    ...
        return: NA
        '''    
        pass  

    
    def run_script(self, script, **kwargs):
        '''
        description:this method is assist OS to run scripts with absolute path
        author: yuhanhou
        params: script, script relative to path tea/test/standalone
                kwargs, optional kw pairs
                        opt_str: cmd options for the script
                        bkground:True or False, default is False
                        program: the language of the scripts, python3, shell, powershell etc
        return: result of the script execution, if bkground is True, nothing returned.
        '''
        #if scripts is py, python + script run

        #if scripts is sh, ...


        pass


    def set_env_var(self):
        '''
        description: set the env of PATH and PYTHONPATH
        author: yuhanhou
        params: NA
        return: NA
        '''   
        pass      


    def shutdown(self):  
        '''
        description: shutdown OS
        author: yuhanhou
        params: NA
        return: NA
        '''   
        pass






