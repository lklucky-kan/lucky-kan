# !/usr/bin/python3
# -*- encoding: utf-8 -*-
import pexpect
import sys
import os
import time

import re


class LoginClass(object):
    def __init__(self, ip=None, username='root', password=None, words=None, user_expt='continue', **kwargs):
        self.ip = ip
        self.username = username
        self.password = password
        self.words = words
        self.user_expt = user_expt
        self.print_out = None
        self.log = None
        # self.cmd_logger = kwargs.get("cmd_logger",lambda _:print("[CMD] %s" % _))
        self.cmd_logger = kwargs.get("cmd_logger", lambda _: _)

    def ssh_login(self, command, timeout=15):
        ssh_timeout = timeout
        ret = 0
        ssh_rst = 0
        self.cmd_logger(command)
        ssh = pexpect.spawn('ssh ' + self.username + '@%s "%s"' % (self.ip, command), timeout=ssh_timeout)
        try:
            i = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout=ssh_timeout)
            if i == 0:
                ssh.sendline(self.password)
                get_rst = ssh.read()
            elif i == 1:
                ssh.sendline('yes\n')
                ssh.expect('password: ')
                ssh.sendline(self.password)
                get_rst = ssh.read()
            ssh_rst = get_rst
            ssh_out = str(ssh_rst, 'utf-8')
            if self.print_out == True:
                print(ssh_out)
            if self.log != None:
                self.log.info(ssh_out)
            ret = 0
        except pexpect.EOF:
            print("EOF Error,SSH login Fail,host IP:" + self.ip + ' Username:%s' %
                  self.username, 'Password:%s' % self.password)
            ssh.close()
            ret = -1
            # sys.exit(-1)
        except pexpect.TIMEOUT:
            print("request timeout")
            ssh.close()
            ret = -2
            print("Please check the host status,ip: " + self.ip)
            # sys.exit(-1)
        except socket.timeout as error:
            print("request timeout")
            ssh.close()
            ret = -2
            print("Please check the host status,ip: " + self.ip)
        return ret, ssh_rst

    def fail_exit(self, user_expt):
        if user_expt == 'continue':
            print("Encounter Fail item,continue next test")
        elif user_expt == 'exit':
            sys.exit(-1)
        else:
            print("unknown argument,neen give user expeted operation <continue> or <exit>")
            sys.exit(-1)

    def ini_telnet(self, rst):  # telnet login by telnetlib
        Fail_login = 0
        output = 0
        try:
            tn = telnetlib.Telnet(self.ip, port=23, timeout=10)
            # tn.set_debuglevel(2)
            tn.read_until('login: ', timeout=5)
            tn.write(self.username + '\n')
            tn.read_until('Password: ', timeout=1)
            tn.write(self.password + '\n')
            tn.read_some()
            result = tn.read_some()
        except socket.error as error:
            print("request timeout")
            print("Please check the host status,ip: " + self.ip)
            Fail_login = 1
            return output, Fail_login
        except Exception:
            print('Telnet connection Fail,IP:%s' % self.ip, 'username:%s' %
                  self.username, 'Password:%s' % self.password)
            # raise err
            Fail_login = 1
            return output, Fail_login
        if result.find('incorrect') != -1:
            print("****** login incorrect!\n", 'please check your user name and password')
            sys.exit(-1)
        elif result.find(rst) != -1 or result.find(':') != -1:
            tn.write(self.command + '\n')
            # tn.read_until('$')
        else:
            print("Telnet No return")
            Fail_login = 1
            return output, Fail_login
        tn.write("exit\n")
        output = tn.read_all()
        tn.close()
        return output, Fail_login

    def tel_in(self, rst):  # telnet by pexpect
        loginName = self.username
        loginPassword = self.password
        loginprompt = rst
        cmd = 'telnet ' + self.ip
        os_cmd = self.command
        child = pexpect.spawn(cmd)
        index1 = child.expect([":", pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        print('index', index1)
        if (index1 == 0):
            child.sendline(loginName)
            index2 = child.expect(["[pP]assword:", pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            child.sendline(loginPassword)
            child.expect(loginprompt)
            print(child.before)
            if (index2 == 0):
                time.sleep(2)
                child.sendline(os_cmd)
                r = child.expect(os_cmd)
                print(r)
                child.expect(loginprompt)
                # child.expect(':' or '$' or '#')
                child.expect('$')
                print(child.before)
            else:
                print("telnet login failed, due to TIMEOUT or EOF")
                child.close(force=True)

    def keywords_check(self, cmd, ssh_out, words, cnt, user_expt):
        ssh_out = str(ssh_out)
        word_find = ''
        clk = ''
        check_result = ''
        words = words.split()
        for keys in words:
            clk = ssh_out.find(keys)
            if clk == -1:
                print('Fail:Not found the keyword ' + keys + ' from output of command:' + cmd)
                print(ssh_out)
                check_result = 0
            else:
                if str(cnt).isdigit() == True:
                    word_find = ssh_out.count(keys)
                    if word_find == int(cnt):
                        check_result = 1
                        # print(ssh_out)
                        Pass_infor = 'Pass:Except:' + str(cnt) + ' "' + str(
                            keys) + '" words,Actual' + ' ' + str(word_find) + ' words'
                        print(Pass_infor)
                    else:
                        check_result = 0
                        Err_infor = 'Fail:Except:' + str(cnt) + ' "' + str(
                            keys) + '" words,Actual' + ' ' + str(word_find) + ' words'
                        print(Err_infor)
                else:
                    Pass_infor = 'Pass:Searched:' + str(keys) + ' word'
                    print(Pass_infor)
                    check_result = 1
        return ssh_out, clk, check_result

    def retry_keyword(self, retry_expt, **retry_pool):
        retry_time = 0
        clk = 1
        while retry_time < int(retry_expt):
            warm_info = "Test Fail,start retry:" + str(retry_time + 1)
            print(warm_info)
            rt_ssh = self.ssh_login(retry_pool['command'])
            keyword_clk = self.keywords_check(
                retry_pool['command'],
                rt_ssh[1],
                retry_pool['words'],
                retry_pool['cnt'],
                retry_pool['user_expt'])
            retry_time = retry_time + 1
            if keyword_clk[1] != -1 and retry_pool['cnt'] == "":
                print(rt_ssh[1])
                retry_info_clk1 = "Test Pass,after retry:" + str(retry_time)
                print(retry_info_clk1)
                break
            else:
                if keyword_clk[2] == 1:
                    print(rt_ssh[1])
                    retry_info_clk2 = "Test Pass,after retry:" + str(retry_time)
                    print(retry_info_clk2)
                    break
            if retry_time >= int(retry_expt):
                clk = 0
                retry_info = "Test Fail,after retry:" + str(retry_expt)
                print(retry_info)
        print(clk)
        return rt_ssh[1], rt_ssh[0], str(retry_time), clk

    def ssh_run(self, command, words, cnt, user_expt, retry_expt, timeout=15):
        retry = 0
        rt0, rt1, rt2, rt3 = None, None, None, None
        rt_ssh = self.ssh_login(command, timeout)
        if rt_ssh[0] != 0:
            while retry < int(retry_expt):
                warm_info = "SSH login Fail,start retry " + str(
                    retry + 1) + ' User:' + self.username + ' Password:' + self.password
                print(warm_info)
                rt_ssh = self.ssh_login(command)
                time.sleep(1)
                retry = retry + 1
                if rt_ssh[0] == 0:
                    break
                if retry >= int(retry_expt):
                    print("ssh login Fail,the test is interrupted")
                    sys.exit(-1)
            if rt_ssh[0] == 0:
                print(rt_ssh[1])
        keyword_clk = self.keywords_check(command, rt_ssh[1], words, cnt, str(user_expt))
        retry_pool = {'command': command, 'ssh_out': rt_ssh[1], 'words': words, 'cnt': cnt, 'user_expt': user_expt}
        rt0, rt1, rt2, rt3 = rt_ssh[1], rt_ssh[0], retry, keyword_clk[2]
        if int(retry_expt) > 0:
            if keyword_clk[1] == -1 or keyword_clk[2] == 0:
                print("start retry:")
                keyword_clk_try = self.retry_keyword(retry_expt, **retry_pool)
                rt0, rt1, rt2, rt3 = keyword_clk_try[0], keyword_clk_try[1], keyword_clk_try[2], keyword_clk_try[3]
        if rt_ssh[0] == 0:
            if keyword_clk[1] != -1 and cnt == '':
                rt3 = 1
                print(rt0)
        return rt0, rt1, rt2, rt3, keyword_clk[2]


class SolConnect:
    # 初始化数据
    def __init__(self, bmc_ip, bmc_user, bmc_pwd):

        self.child = None
        self.bmc_ip = bmc_ip
        self.bmc_user = bmc_user
        self.bmc_pwd = bmc_pwd
        self.count = 30

    # sol连接
    def conn_sol(self):
        i = 0
        while i < self.count:
            child = pexpect.spawn(
                "ipmitool -I lanplus -H {ip} -U {user} -P {pwd} sol activate".format(ip=self.bmc_ip, user=self.bmc_user,
                                                                                     pwd=self.bmc_pwd))
            index = child.expect_exact(['[SOL Session operational.  Use ~? for help]', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                self.child = child
                break
            else:
                os.system("ipmitool -I lanplus -H {ip} -U {user} -P {pwd} sol deactivate".format(ip=self.bmc_ip,
                                                                                                 user=self.bmc_user,
                                                                                                 pwd=self.bmc_pwd))
                i += 1
                time.sleep(10)
                if i >= self.count:
                    sys.exit(-1)

    # 关闭、断开sol
    def exit_sol(self):
        os.system(
            "ipmitool -I lanplus -H {ip} -U {user} -P {pwd} sol deactivate".format(ip=self.bmc_ip, user=self.bmc_user,
                                                                                   pwd=self.bmc_pwd))
        self.child.close()

    def enter_os(self):
        child = self.child
        i = 0
        index = child.expect(["login:", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        while index != 0 and i < 1500:
            i += 5
            index = child.expect(["login:", pexpect.EOF, pexpect.TIMEOUT], timeout=5)
            if i % 100 == 0:
                child.send('\r')

        time.sleep(60)

        if index == 0:
            return True
        else:
            return False


def exe_sol(ip, user, pwd):
    ssh = SolConnect(ip, user, pwd)
    ssh.conn_sol()
    result = ssh.enter_os()
    ssh.exit_sol()
    if not result:
        sys.exit(-1)


def exe_ssh(ip, user, pwd):
    count = 20
    try:
        ssh_do = LoginClass(ip, user, pwd, cmd_logger=print)

        while count > 0:
            get_rst = ssh_do.ssh_run("cat /root/power_cycle_end_flag.log", "", 1, "continue", 0)
            out = str(get_rst[0])
            # data = ssh.run("cat /root/power_cycle_end_flag.log", i_exit_code=True)
            result = re.findall(r"cycle=pass", out, re.I)
            if result:
                for i in range(3):
                    ssh_do.ssh_run("rm -rf /root/power_cycle_end_flag.log /dev/null", "", 1, "continue", 0)
                    time.sleep(7)
                break
            else:
                time.sleep(60)
                count -= 1
        else:
            return False
    except Exception as err:
        return False

    return True


if __name__ == "__main__":
    ip = sys.argv[1]
    user = sys.argv[2]
    pwd = sys.argv[3]

    res = exe_ssh(ip, user, pwd)
    if not res:
        sys.exit(-1)
