import os
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from ftplib import FTP
from smb.SMBConnection import SMBConnection
from common.other.log import Logger
from common.communication.session import Session


class FileTransfer(Session):
    '''
    description: this class is handling file transfer between hosts.
    author: yuhanhou
    '''

    def __init__(self, **kwargs):
        Session.__init__(self, **kwargs)
        self.key_file = kwargs.get('key_file') #can be used by scp

        if self.logger == None:
            self.logger = Logger(**kwargs)

        self.kwargs = kwargs # used by other customized options depending on protocol

    def scp(self, local, remote, operation='upload'):
        '''
        description: scp files
        author: yuhanhou
        params: local: local path  
                remote: remote path
                operation: upload(default)|download, upload local to remote, or download remote to local.

        return: NA
        '''

        if self.ip == None:
            self.logger.error('ip is not provided!')
            raise Exception('the remote ip is not provided for scp!')

        if self.user == None:
            self.user = 'root'
        
        if self.password == None and self.key_file == None:
            self.password = 'open1sys'


        connection = SSHClient()
        connection.load_system_host_keys()
        connection.set_missing_host_key_policy(AutoAddPolicy())
        connection.connect(self.ip, port=22, key_filename=self.key_file, username=self.user, password=self.password)

        # SCPCLient takes a paramiko transport as an argument
        scp_conn = SCPClient(connection.get_transport())

        if operation == 'upload':
            self.logger.info('uploading ' + local + ' to ' + self.ip +':' + remote)
            scp_conn.put(local, recursive=True, remote_path=remote)
            
        else:
            self.logger.info('downloading ' + self.ip +':' + remote + ' to ' + local)
            scp_conn.get(remote, local_path=local, recursive=True)

        scp_conn.close()
        connection.close()
        

    def samba(self, local, remote, operation='upload', **kwargs):
        '''
        description: support samba protocal to upload/download from samba server
        author: yuhanhou
        params: local, local path, for upload, the path can be file or dir, for download, the path should be dir
                remote, samba server file or dir path,like share_dir/sub_dir/zz, for upload, the path should be dir, for download, the path can be file or dir
                operation, upload or download
        return: NA
        '''

        if self.ip = None:
            self.logger.error('samba server ip is not provided!')
            raise Exception('samba server ip is not provided!')

        if self.user = None:
            self.user = 'anonymous'
        
        if self.port == None:
            self.port = 139
        
        if self.password == None:
            self.password = ''

        conn = SMBConnection(self.user, self.password, 'any', '')
        conn.connect(self.ip, self.port, timeout=self.timeout)

        #get the share dir on samba from the remote path:
        smb_share_dir = remote_path.split('/').pop(0)
        #change the path sep in remote path to the current os sep:
        relative_path_in_share = re.sub(smb_share_dir + r'/?', '', remote_path) #change remote to relative path to the share dir
        relative_path_in_share = relative_path_under_share.replace('/', os.sep)

        if operation == 'upload': # put the local path content to the remote path
            #if the local path is a file path
            if os.path.isfile(local):
                success = self.smb_upload_single_file(conn, local, relative_path_in_share, smb_share_dir, timeout)
                if not success:
                    self.logger.error('can\'t upload ' + local + ' to ' + remote)

            #if the local path is a dir path, maybe include subdirs, need upload the whole dir to the remote path
            elif os.path.isdir(local):
                local = local.rstrip(os.sep) # for c:\\test\\ need to remote the last \\
                dir_name = os.path.basename(local)
                remote_dir_path = os.path.join(relative_path_in_share, dir_name)
                conn.createDirectory(smb_share_dir, remote_dir_path) #create the dir on remote path
                
                for dir_path, dirs, files in os.walk(local):
                    for f in files:
                        file_path = os.path.join(dir_path, f)
                        sub_remote_dir_path = remote_dir_path
                        
                        if not os.path.samefile(local, dir_path):
                            sub_dir = os.path.relpath(dir_path, start=local)
                            sub_remote_dir_path = os.path.join(remote_dir_path, sub_dir)
                        
                        success = self.smb_upload_single_file(conn, file_path, remote_dir_path, smb_share_dir, timeout)


        else:
            pass





    def ftp(self, local, remote, operation='upload', **kwargs):
        pass

    def nfs(self, local, remote, operation='upload', **kwargs):
        pass






    def upload(self, local, remote, protocol='scp', **kwargs):
        '''
        description: scp files
        author: yuhanhou
        params: local: local path  
                remote: remote path
                protocol: upload protocol, scp|ftp|nfs|samba
                kwargs: remote options of the transfer
                        ip:  mandatory
                        user:
                        password:
                        key_file: 
                        timeout: 900(default), timeout of the scp transfer, seconds.
                        port, depend on which protocol is used
        return: NA 
        '''

        if protocol == 'scp':
            self.scp(local, remote, operation='upload', **kwargs)
        elif protocol == 'ftp':
            self.ftp(local, remote, operation='upload', **kwargs)
        elif protocol == 'nfs':
            self.nfs(local, remote, operation='upload', **kwargs)
        elif protocol == 'samba':
            self.samba(local, remote, operation='upload', **kwargs)
        else:
            self.logger.warn(protocol, 'is not supported!')


    def download(self, local, remote, protocol='scp', **kwargs):
        '''
        description: scp files
        author: yuhanhou
        params: local: local path  
                remote: remote path
                protocol: download protocol, scp|ftp|nfs|samba
                kwargs: remote options of the transfer
                        ip:  mandatory
                        user:
                        password:
                        key_file: 
                        timeout: 900(default), timeout of the scp transfer, seconds.
                        port, depend on which protocol is used

        return: NA 
        '''

        if protocol == 'scp':
            self.scp(local, remote, operation='download', **kwargs)
        elif protocol == 'ftp':
            self.ftp(local, remote, operation='download', **kwargs)
        elif protocol == 'nfs':
            self.nfs(local, remote, operation='download', **kwargs)
        elif protocol == 'samba':
            self.samba(local, remote, operation='download', **kwargs)
        else:
            self.logger.warn(protocol, 'is not supported!')