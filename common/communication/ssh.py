import pexpect
import re
import os, sys
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
    )
)
from common.communication.session import Session

class SSH(Session):
    '''
    description: This is a ssh class to support ssh connection 
    author: yuhanhou
    '''

    def __init__(self, port=22, prompt=r'\n*\r*[^#]\S+@\S+\s*\S*]#\s*', **kwargs):
        Session.__init__(self, **kwargs)
        self.port = port
        self.prompt = prompt
         
        self.key_file = kwargs.get('key_file', '')
        self.question = '(?i)are you sure you want to continue connecting'
        #bad connection when the OS is reinstalled. need to clear the known host file
        
        self.open()    

    def open(self):
        '''
        description: open session to the remote system
        author: houyuhan
        params: N/A
        return: N/A
        '''
        self.logger.info('trying to open ssh session of ' + self.ip + '...')
        spawn_ssh = "ssh " + self.key_file + self.user + '@' + self.ip + " -p " + str(self.port)
         
        self.logger.info(spawn_ssh)
        self.session = pexpect.spawn(spawn_ssh, timeout=self.timeout)
        if os.environ.get('DEBUG'):
            log_file = self.ip + 'pexepct_debug.log'
            fh = open(log_file, 'wb+')
            self.session.logfile = fh
        
        
        retry = 0
        send_passwd_count   = 0

        while True :
            index = self.session.expect([pexpect.EOF, pexpect.TIMEOUT, self.question, 'assword:', r'yes\S+no.*' ,self.prompt])

            self.logger.debug("in expect open_session")
            if index == 0:
                #if failed to spawn session, try 3 times
                retry += 1
                if retry > 3:
                    self.logger.error("ACCESS ERROR: failed to spawn to " + self.ip)
                    raise Exception("ACCESS ERROR: failed to spawn to " + self.ip)
                
                self.logger.info("try to connect again, %d" % retry + " times")
                self.session = pexpect.spawn(spawn_ssh)
                continue

            if index == 1:#timeout
                self.logger.error('ACCESS ERROR! ' + self.session.before.decode())
                raise Exception('ACCESS ERROR! ' + self.session.before.decode())
           
            if index == 2: # In this case SSH does not have the public key cached.
                self.logger.info("save the key")
                self.session.sendline ('yes')
                continue

            if index == 3: #need password
                if send_passwd_count >= 1:
                    self.logger.error("ACCESS ERROR: password is not correct")
                    raise Exception('ACCESS ERROR: password is not correct')

                self.logger.info("sending password")
                self.logger.debug(self.password)
                self.session.sendline (self.password)
                send_passwd_count += 1
                continue
            
            if index == 4:
                self.session.sendline ('yes')
            
            if index == 5:
                self.logger.info("session is successfully open")
                break
                
                

    def cmd(self, cmd_line, **kwargs):
        '''
        description: send cmd and get return
        author: houyuhan
        params: cmd_line, the cmd line need to send to the remote system
                kwargs, options need to customized to the session
                      return_list: 0 or 1(default)cmd result into list by lines or not
                      prompt: the cmd done prompt expression
                      get_match: True or False(default), get the matched prompt line into the result or not
        return: cmd result
        '''

        return_list = kwargs.get('return_list', True)
        prompt = kwargs.get('prompt', self.prompt)
        #prompt = r'\n*\r*\S+\s*]#' #daisy
        retry = 0
        result = ''
            
        while True:
            
            #check session status, re-open if needed.
            if (not self.session.isalive() or not self.session):
                self.session = None
                self.logger.error("Session issue")
                self.logger.info("try re-connect to system...")
                self.open()
                
                
            self.logger.info(self.ip + " sending command: " + cmd_line)
            self.logger.debug('prompt:' + prompt)
            self.session.sendline(cmd_line)

            index = self.session.expect([pexpect.EOF, pexpect.TIMEOUT, prompt])

            if index == 0 or index == 1:
           
                self.logger.error("session response timeout")

                if retry == 1:
                    result = []
                    break
                else:
                    retry = retry + 1
                    continue
            if index == 2:
 
                result = self.session.before
                #print(result) #daisy

                result = result.decode()
                
                if kwargs.get('get_match') == True:#get the matched prompt line
                    result += '\n' + (self.session.match.group(0)).decode()
                
                result = result.strip()
            
                result = [l.strip() for l in re.split('[\r\n]+', result)]
                
                del result[0] # to remove the command string itself
                # To remove the last prompt line
                #lines = len(result)
                #del result[lines-1] 
                break

        
        self.logger.info('\n' + '\n'.join(result))
                
        if not return_list:
            result = '\n'.join(result)
                
        return result



    def close(self):
        self.session.close()

