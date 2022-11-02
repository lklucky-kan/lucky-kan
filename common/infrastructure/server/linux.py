import re
import os
import os, sys
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir,
        os.pardir
    )
)
from common.communication.ssh import SSH
from common.communication.local import Local
from common.infrastructure.server.os import OS

class Linux(OS):
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
                        protocol, remote connection protocol,supported is ssh, local
                        port, protocol related port, like ssh is 22
                        logger, logger object, optional, default is using log file with the ip address and timestemp
        '''
        if 'scripts_root_path' not in kwargs:
            kwargs.update(scripts_root_path='/scripts')
            
        OS.__init__(self, path_sep='/',**kwargs)

        self.user = kwargs.get('user', 'root')
        self.password = kwargs.get('password', 'open1sys')
        self.protocol = kwargs.get('protocol', 'ssh')
        self.mount_point =kwargs.get('mount_point', '/samba')

        if re.search('ssh', self.protocol, re.I):
            session_opts = kwargs.copy()
            session_opts.update(user=self.user, password=self.password, logger=self.logger)
            # self.logger.debug('session_opts:\n' + str(session_opts))
            self.session = SSH(**session_opts)
        elif re.search('local', self.protocol, re.I):
            self.session = Local(logger=self.logger)
    
        # self.set_env_var()
        



    def set_env_var(self):
        '''
        description: set the env of PATH and PYTHONPATH
        author: yuhanhou
        params: NA
        return: NA
        '''
        out = self.cmd("cat /etc/profile | grep -E 'export (PATH|PYTHONPATH)='", return_list=False)
        if not re.search('PYTHONPATH=.*'+self.tea_path, out):
            #current_tea_path = self.scripts_root_path
            #if self.protocol == 'local':
            #    cur_path = os.getcwd()
            #    match = re.search(r'^(\S+tea)', cur_path)
            #    if match:
            #        current_tea_path = match.group(1)

            cmdline = "echo 'export PYTHONPATH=" + self.tea_path + ":.' >> /etc/profile" 
            #cmdline = "export PYTHONPATH=.:" + self.tea_path" 
            self.cmd(cmdline)
            self.cmd('source /etc/profile')
        
        if not re.search('PATH=' + self.scripts_root_path, out): #implement in future if needed.
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
        self.cmd('reboot')


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
                kwargs, optional 
                    user: smba user
                    password: 
                    mount_point, default is /samba
        return: NA
        '''
        #//192.168.56.135/shared on /tmp/mm type cifs 
        #check mount first
        ip, share_dir = smb_share.split(':')

        output = self.cmd('mount | grep //' + ip + '/' + share_dir + ' --color=never' , return_list=False)
        match = re.search(share_dir + r' on (\S+)', output, re.I)


        if match:
            mount_point = match.group(1)
        else: #mount the share dir
            mount_point = kwargs.get('mount_point', self.mount_point)
            #create mount point if not exist
            output = self.cmd('ls -l ' + mount_point + ' --color=never', return_list=False)
            if re.search('No such', output, re.I):
                self.cmd('sudo mkdir ' + mount_point)
            
            mount_opts = ''
            if kwargs.get('user'):
                mount_opts += ' -o username=' + kwargs.get('user')
            
            if kwargs.get('password') and kwargs.get('password') != '':
                mount_opts += ' -o password=' + kwargs.get('password')
            else:
                mount_opts += " -o password=''" 

            self.cmd('sudo mount -t cifs' + mount_opts + ' //' + ip + '/' + share_dir + ' ' + mount_point)
            #can add check mount result in future
        
        self.mount_point = mount_point
        
        return mount_point


    def raw_copy(self, src, des, **kwargs):
        '''
        description: this method is used by OS copy cmd, the src file or dir copied into des dir
        author: yuhanhou
        params: src, source file or dir
                des, target dir, des must be a dir
                kwargs, optional kw pairs
                    chmod:'755'
        return: NA
        '''


        #out = self.cmd('ls -l ' + des + ' --color=never', return_list=False)
        #if re.search('no such', out, re.I):
        if not os.path.isdir(des):
            self.cmd('sudo mkdir -p ' + des)

        self.cmd('sudo cp -ru ' + src + ' ' + des)

        if kwargs.get('chmod'):
            self.cmd('sudo chmod 755 -R ' + des)
        
        
        
             
    def clear_tea_scripts(self):
        '''
        description: clean tea under scripts_root_path  
        author: yuhanhou
        params: NA
        return: NA
        '''

        cmdline = 'rm -rf ' + self.tea_path
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

        self.raw_copy('/var/log/messages', self.local_log_path)  


    def run_script(self, script, **kwargs):
        '''
        description:this method is assist OS to run scripts with absolute path
        author: yuhanhou
        params: script, script relative to self.scripts_root_path
                kwargs, optional kw pairs
                        opts: cmd options for the script
                        bkground:True or False, default is False
                        program: the language of the scripts, python3, shell, powershell etc
        return: result of the script execution, if bkground is True, nothing returned.
        '''

        #tea_path is defined in os.py, it's tea's abs path
        cmdline = self.tea_path + self.path_sep + script + ' ' + kwargs.get('opts', '')
        # self.logger.info(cmdline)
        #if scripts is py, python + script run
        if kwargs.get('program') == 'python3':
            cmdline = 'python3 ' + cmdline

        #if scripts is sh, ...


        if kwargs.get('bkground', False):
            if isinstance(self.session, Local):
                with open(f'{kwargs.get("name")}_nohup.out','w')as fw:
                    return self.session.bk_cmd(cmdline, stdout=fw)

            nohup_out = self.tea_path + self.path_sep + f'{kwargs.get("name")}_nohup.out'
            cmdline = 'nohup ' + cmdline + f' > {nohup_out} 2>&1 &'
        
        return self.cmd(cmdline, return_list=False)



    def shutdown(self):
        self.cmd('shutdown -h now')
