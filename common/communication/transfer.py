import os, shutil
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from ftplib import FTP
#from smb.SMBConnection import SMBConnection
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

    def scp(self, local, remote, operation='upload', **kwargs):
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
        
    @classmethod
    def copy_files(cls, src, des):
        '''
        description: copy files from src to des, can be used to nfs/smb upload/download
        author: yuhanhou
        params: src, source file or dir to copy
                des, target dir or file, if src is dir, des should be also dir
        return: NA
        '''

        if os.path.isfile(src):
            shutil.copy(src, des)
        elif os.path.isdir(src):
            dir_name = os.path.basename(src.rstrip(os.sep))
            shutil.copytree(src, os.join.path(des, dir_name))  

 

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
