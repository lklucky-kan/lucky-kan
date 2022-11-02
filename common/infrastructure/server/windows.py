import re
from datetime import datetime
from common.communication.winrm import Winrm
from common.communication.local import Local
from common.infrastructure.server.os import OS
from common.other.log import Logger

class Windows(OS):
    '''
    description: this class is the parent class for linux OS, like rhel, sles, ubantu
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
        if 'scripts_root_path' not in kwargs:
            kwargs.update(scripts_root_path='c:\\scripts')
            
        OS.__init__(self, path_sep=r'\\', **kwargs)

        self.user = kwargs.get('user', 'Administrator')
        self.password = kwargs.get('password', 'Open1sys!')
        self.protocol = kwargs.get('protocol', 'winrm')
        self.mount_point = kwargs.get('mount_point', 's:')
        


        #create session:
        if re.search('winrm', self.protocol, re.I):
            session_opts = kwargs.copy()
            session_opts.update(user=self.user, password=self.password,logger=self.logger)
            self.session = Winrm(**session_opts)
        elif re.search('local', self.protocol, re.I):
            self.session = Local(encoding='ANSI', logger=self.logger)


    def set_env_var(self):
        '''
        description: set the env of PATH and PYTHONPATH
        author: yuhanhou
        params: NA
        return: NA
        '''
        pass


    def reboot(self, method='inband'):
        '''
        description: reboot os
        author: yuhanhou
        params: method, inband or outband
        return: NA
        '''
        if method == 'inband':
            self.reboot_inband()
        elif method == 'outband':
            self.reboot_outband()
        else:
            self.logger.error(method + ' is not supported for rebooting!')



    def reboot_inband(self):
        '''
        description: reboot os inband
        author: yuhanhou
        params: NA
        return: NA
        '''        
        self.cmd('shutdown /r /t 0')


    def reboot_outband(self):
        '''
        description: reboot os out of band
        author: yuhanhou
        params: NA
        return: NA
        '''             
        pass 


    def mount_smb(self, smb_share, **kwargs):
        '''
        description:
        author: yuhanhou
        params: smb_share, ip:share_dir
                share_dir, shared dir of smb server
                kwargs, optional 
                    user: smba user
                    password: 
                    mount_point, default is /samba
        return: NA
        '''

        ip, share_dir = smb_share.split(':')

        #OK           H:        \\192.168.56.135\shared   Microsoft Windows Network
        #OK           H:        \\192.168.56.135\shared   Microsoft Windows Network
        #check mount first
        output = self.cmd('net use', return_list=False)
        share_path  =  r'\\\\' + ip + r'\\' + share_dir
        need_mount = 0

        if re.search(share_path + r'\s+', output):
            match = re.search(r'[\r\n]+(\S+)\s+(\S+)\s+' + share_path, output, re.I)

            if match:
                mount_status = match.group(1)
                mount_point = match.group(2)
                if re.search('ok', mount_status, re.I):
                    self.mount_point = mount_point
                else:
                    self.cmd('net use ' + mount_point + ' /del')
                    need_mount = 1
                    
            elif re.search(r'[\r\n]+\S+\s+' + share_path, output, re.I): #maybe no mapping disk char, maybe connect is not ok
                #del the invaild mount:
                self.cmd('net use ' + share_path + ' /del')
                need_mount = 1
        else:
            need_mount = 1

        
        if need_mount: 
            #net use \\IP\ipc$ "PASSWORD" /USER:"USERNAME" 
            mount_opts = ''
            if kwargs.get('password'):
                mount_opts += ' ' + kwargs.get('password')
            else:
                mount_opts += ' ""'  
            
            if kwargs.get('user'):
                mount_opts += ' /USER:' + kwargs.get('user')
            
            mount_point = kwargs.get('mount_point', self.mount_point)
            self.cmd('net use ' + mount_point + ' ' + share_path + mount_opts, return_list=False)
            #can add check mount result in future
            self.mount_point = mount_point
            
            return mount_point


    def raw_copy(self, src, des):
        '''
        description: this method is used by OS copy cmd, the src file or dir copied into des dir
        author: yuhanhou
        params: src, source file or dir
                des, target dir, not support rename src file yet.
        return: NA
        '''

        cmdline = 'xcopy ' + src 

        out = self.cmd('dir ' + src, shell=True)

        #check if src is a file or dir:
        if re.search('<DIR>', out, re.I):
            src = src.rstrip(self.path_sep)
            dir_name = src.split(self.path_sep).pop()

            cmdline += ' ' + des + self.path_sep + dir_name + self.path_sep + ' /S'
        else:
            cmdline += ' ' + des + self.path_sep

        
        self.cmd(cmdline, shell=True)

    
    def clear_tea_scripts(self):
        '''
        description: clear the tea under scripts path of the server
        author: yuhanhou
        params: NA
        return: NA
        '''

        cmdline = 'rd /s /q ' + self.tea_path
        self.cmd(cmdline)
        


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
        params: script, script relative to self.scripts_root_path
                kwargs, optional kw pairs
                        opt_str: cmd options for the script
                        bkground:True or False, default is False
                        program: the language of the scripts, python3, shell, powershell etc
        return: result of the script execution, if bkground is True, nothing returned.
        '''
        #if scripts is py, python + script run

        #if scripts is sh, ...


        pass