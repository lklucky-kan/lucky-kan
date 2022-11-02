import subprocess
import os
import sys
import time
import multiprocessing
import re

# matplotlib
from mudan_disk_fio_config import *
from matplotlib import pyplot
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import namedtuple
from ReportHelper import *

workpath = os.path.dirname(os.path.realpath(__file__))
reports_path = f"{workpath}/reports/"


def draw_speed_info(disk_list, bs, runtype):
    lspci = {}
    for dev in disk_list:
        sdisk = dev.split("/")[-1]
        dev_path = f"{reports_path}{sdisk}/{bs}_{runtype}_speed.log"
        for checkword in ["LnkCap", "LnkSta", "LnkCtl2"]:
            num_list = []
            lspci_info = command(f"cat {dev_path}|grep -i {checkword}").output
            info = lspci_info.splitlines()
            s = False
            for speedlines in info:
                speedline = speedlines.split()
                for speed in speedline:
                    if s:
                        num = re.search("\d+(\.\d+)?", speed)
                        if not num[0]:
                            num = re.search("\d+", speed)
                        num_list.append(num[0])
                        s = False
                        break
                    if "Speed" in speed or "speed" in speed and "SpeedDis" not in speed:
                        s = True
            lspci[checkword] = num_list
            print(num_list)
            print(lspci)
    draw(lspci["LnkCtl2"], lspci["LnkCap"], lspci["LnkSta"], dev_path)


def draw(lnkctl2, lnkcap, lnksta, path):
    pyplot.figure(figsize=(6, 6), dpi=80)
    lnkctl2 = [float(x) for x in lnkctl2]
    lnkcap = [float(x) for x in lnkcap]
    lnksta = [float(x) for x in lnksta]
    path = path.split("/")
    path[-1] = path[-1].split(".")[0]
    path = "/".join(path)
    x = [x for x in range(len(lnkctl2))]
    ax1 = pyplot.subplot(221)
    pyplot.plot(x, lnkcap)
    ax2 = pyplot.subplot(222)
    pyplot.plot(x, lnksta)
    ax3 = pyplot.subplot(212)
    pyplot.plot(x, lnkctl2)
    ax1.title.set_text("lnkcap")
    ax2.title.set_text("lnksta")
    ax3.title.set_text("lnkctl2")
    pyplot.savefig(path)


def save_lsscsl():
    # save lsscsl info
    print(f"save lsscsi > {reports_path}lsscsi")
    command(f"lsscsi -gt > {reports_path}lsscsi.log")


def save_smart(disk_list, disktype, path="before"):
    for dev in disk_list:
        if disktype == "nvme":
            smart_info = command(f"nvme smart-log {dev}").output
        else:
            smart_info = command(f"smartctl -a {dev}").output
        sdisk = dev.split("/")[-1]
        if smart_info:
            savelog(
                f"====== get smart log {path}=======", f"{sdisk}/{sdisk}smartinfo.log"
            )
            savelog(smart_info, f"{sdisk}/{sdisk}smartinfo.log")
        else:
            savelog("get smart log is fail ", f"{sdisk}/{sdisk}smartinfo.log")


def run_mult(disk_list, disktype, bs_list, runtype, bs_value, funname):
    p = multiprocessing.Pool(len(disk_list) * len(bs_list))
    for dev in disk_list:
        sdisk = dev.split("/")[-1]
        p.apply_async(
            func=funname,
            args=(
                disktype,
                sdisk,
                bs_value,
                runtype,
            ),
        )
        p.close()
        time.sleep(10)
    return p


def get_speed(devtype, sdev, bs, runtype):
    dictinfo = {}
    i = 1
    checkinfo = None
    if devtype == "nvme":
        busid = command(
            "readlink -f /sys/block/%s |grep -oE '[a-zA-Z0-9]{4}\:[a-zA-Z0-9]{2}\:[a-zA-Z0-9]{2}\.[a-zA-Z0-9]+'| tail -1"
            % sdev
        ).output
        print("getting speed info ....")
        while True:
            lnkcap = command(f"lspci -s {busid} -vvv |grep -i lnkcap:").output
            lnksta = command(f"lspci -s {busid} -vvv |grep -i lnksta:").output
            lnkctl2 = command(f"lspci -s {busid} -vvv |grep -i lnkctl2:").output
            if i == 1:
                checklnkcap = lnkcap
                checklnksta = lnksta
                checklnkct12 = lnkctl2
            dev_path = f"{sdev}/{bs}_{runtype}_speed.log"
            savelog(f" ==== get {i} SPEED  info ===== \n", dev_path)
            savelog(lnkcap, dev_path)
            savelog(lnksta, dev_path)
            savelog(lnkctl2, dev_path)
            if (
                lnkcap != checklnkcap
                or lnksta != checklnksta
                or lnkctl2 != checklnkct12
            ):
                dev_path = f"{sdev}/{bs}_{runtype}_error_speed.log"
                savelog(f" ==== check {i} SPEED  info is error  ===== \n", dev_path)
                savelog(lnkcap, dev_path)
                savelog(lnksta, dev_path)
                savelog(lnkctl2, dev_path)
            time.sleep(1)
            i += 1

    else:
        while True:
            speed_info = command(f"smartctl -a /dev/{sdev} |grep -i sata").output
            if i < 2:
                checkinfo = speed_info
            if speed_info == checkinfo:
                dev_path = f"{sdev}/{bs}_{runtype}_speed.log"
                savelog(f"\n ==== get {i} speed  info ===== \n", dev_path)
                savelog(speed_info, dev_path)
            else:
                dev_path = f"{sdev}/{bs}_{runtype}_error_speed.log"
                savelog(f"\n ==== check {i} speed  info is error  ===== \n", dev_path)
                savelog(speed_info, dev_path)
            time.sleep(1)
            i += 1


def get_temp_log(disktpye, sdev, bs, runtype):
    print(f"save {sdev}/{bs}_{runtype}_temp.log")
    while True:
        if disktpye == "nvme":
            temp_info = command(f"nvme smart-log /dev/{sdev} |grep temperature").output
            savelog(temp_info, f"{sdev}/{bs}_{runtype}_temp.log")
        else:
            temp_info = command(
                f"smartctl -a /dev/{sdev} |grep -iE 'Current Drive Temperature|Temperature_Celsius'"
            ).output
            filter_info = re.findall("min/max", temp_info, re.I)
            if filter_info:
                savelog(filter_info[0], f"{sdev}/{bs}_{runtype}_temp.log")
            else:
                savelog(temp_info, f"{sdev}/{bs}_{runtype}_temp.log")
        time.sleep(10)


def make_dir(reports_path, fpass=False):
    # create reports dir
    if os.path.exists(reports_path):
        if fpass:
            return
        if input(f"Are you want to remove {reports_path} (Y/N):") != "N":
            os.system(f"rm -rf {reports_path}*")
    else:
        os.system(f"mkdir {reports_path}")
        time.sleep(1)


def savelog(info, logname="logs.log", mode="a"):
    # save log info func
    nowtime = time.strftime("%Y%m%d-%H-%M-%S")
    if mode == "a" or mode == "w":
        with open(f"{reports_path}{logname}", mode) as fw:
            fw.write(f"{nowtime} : {info}  \n")


def command(command, log=True):
    """
    Execute OS system command
    :param command: system command can be executed in Linux Shell or Windows Command Prompt
    author: zhuangzhao
    """
    if not isinstance(command, str):
        raise TypeError(
            f"command MUST be _cmd string type, {command} is _cmd {type(command)} type"
        )
    SysCMD = namedtuple("SysCMD", ["returncode", "output"])
    savelog(f'This is running "{command}" on localhost')
    p = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    # p.wait(5)
    stdout = p.communicate()[0].strip()
    if p.poll() != 0:
        stderr = p.poll()
        savelog(f"Error : The command return stderr is {stderr}")
    else:
        if log:
            savelog(f"The command return is {stdout}")
            pass
    return SysCMD(p.returncode, stdout)


def check_smart(devlist):
    sarmtpath = f"{reports_path}smartlog/"
    command(f"mkdir {sarmtpath}")
    for dev in devlist:
        hctl = command("lsscsi -gt |grep  '%s' |awk '{print $1}'" % dev).output[1:-1]
        output = command(f"smartctl -H {dev} ").output
        savelog(output, f"smartlog/{hctl}smart.log")
        if command(f'smartctl -H {dev} |grep -iE ": ok|: pass"').output:
            # check info
            print(f"check {dev} smart log is pass ")
        else:
            input(
                f"check {dev} smart log is fail , Press CTRL + C to exit or Enter continue "
            )


def nohup(cmd, name="nohup.log"):
    # get running process id
    pids = []
    output = command(
        "ps -ef | grep -i '%s' |grep -v grep |awk '{print $2}'" % cmd, False
    ).output.splitlines()
    for proc in output:
        pid = proc.split()[0]
        pids.append(pid)
    command(f"nohup {cmd} >> {name} 2>&1 &", False)
    print(f"run : {cmd}")
    time.sleep(5)
    outputs = command(
        "ps -ef | grep -i '%s' |grep -v grep |awk '{print $2}'" % cmd
    ).output.splitlines()
    if outputs:
        for pid in outputs:
            if pid not in pids:
                print(f"run nohup process is sucessful pid is {pid}")
                return pid
    else:
        savelog(" nohup is not successful ")
        pass
    return 999999999


def get_iostat_log(disk_list, bs_value, runtype):
    pid_list = []
    iostat_logs = []
    for dev in disk_list:
        sdisk = dev.split("/")[-1]
        dev_path = f"{reports_path}{sdisk}/"
        iostat_log = f"{dev_path}{bs_value}_{runtype}_iostat.log"
        pid2 = nohup(f"iostat -x -t 1", f"{iostat_log}")
        pid_list.append(pid2)
        iostat_logs.append(iostat_log)
    return pid_list, iostat_logs


def wait_process(task, timeout=0):
    waittime = 0
    print(f"wait pid is {task} process is end ")
    while True:
        process = command('ps -ef | grep -i "%s" | grep -v grep' % task).output
        if process:
            time.sleep(30)
            waittime += 30
            if timeout and waittime >= timeout:
                savelog("after %s second, task %s still exist" % (timeout, task))
                raise Exception(
                    "after %s second, task %s still exist" % (timeout, task)
                )
        else:
            savelog(f"{task} process is finish")
            savelog(f"{task} process is ran {waittime}s")
            break


def kill_process(pid):
    command(f"kill -8 {pid}")
    savelog(f"kill process pid is {pid}")


def get_temp_num(disktpye, path, sdev):
    if disktpye == "nvme":
        temp_num = command("cat %s |awk '{print $5}'" % path).output.split()
    else:
        info = command(
            f"smartctl -a /dev/{sdev} |grep -iE 'Current Drive Temperature|Temperature_Celsius'"
        ).output
        filter_info = re.findall("min/max", info, re.I)
        if filter_info:
            temp_num = command("cat %s |awk '{print $12}'" % path).output.split()
        else:
            temp_num = command("cat %s |awk '{print $6}'" % path).output.split()
    draw_temp(temp_num, path)


def draw_temp_info(disk_list, disktype, bs_value, runtype):
    for dev in disk_list:
        sdisk = dev.split("/")[-1]
        path = f"{reports_path}{sdisk}/{bs_value}_{runtype}_temp.log"
        get_temp_num(disktype, path, sdisk)


def draw_temp(data, path):
    pyplot.figure(figsize=(5, 5), dpi=80)
    runtype_data = [float(x) for x in data]
    path = path.split("/")
    path[-1] = path[-1].split(".")[0]
    path = "/".join(path)
    x = [x for x in range(len(runtype_data))]
    pyplot.plot(x, runtype_data)
    pyplot.savefig(path)


def draw_iostat_info(iostat_logs, disk_list):
    iostat_info = command("iostat -x |grep -i device").output.split()
    iostat_dict = {}
    weight = 1
    for info in iostat_info:
        if info == "r/s":
            read = weight
        elif info == "w/s":
            write = weight
        elif info == "rkB/s" or info == "rMB/s":
            randread = weight
        elif info == "wkB/s" or info == "wMB/s":
            randwrite = weight
        elif info == "r_await":
            r_await = weight
        elif info == "w_await":
            w_await = weight
        weight += 1

    for iostat in iostat_logs:
        for dev in disk_list:
            sdisk = dev.split("/")[-1]
            if sdisk in iostat:
                if runtype["runtype"] == "write":
                    write_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, write)
                    ).output.split()
                    writebw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'"
                        % (iostat, sdisk, randwrite)
                    ).output.split()
                    iostat_dict[sdisk] = [
                        {"测试1": [{"IOPS": write_info}, {"BW": writebw_info}]}
                    ]

                elif runtype["runtype"] == "read":
                    read_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, read)
                    ).output.split()
                    readbw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, randread)
                    ).output.split()
                    iostat_dict[sdisk] = [
                        {"测试2": [{"IOPS": read_info}, {"BW": readbw_info}]}
                    ]

                elif runtype["runtype"] == "mix_readwrite":
                    write_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, write)
                    ).output.split()
                    read_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, read)
                    ).output.split()
                    writebw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'"
                        % (iostat, sdisk, randwrite)
                    ).output.split()
                    readbw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, randread)
                    ).output.split()
                    read_write = [
                        float(x) + float(y) for x, y in zip(read_info, write_info)
                    ]
                    randread_randwrite = [
                        float(x) + float(y) for x, y in zip(writebw_info, readbw_info)
                    ]
                    iostat_dict[sdisk] = [
                        {
                            "测试3": [
                                {"IOPS_R": read_info},
                                {"IOPS_W": write_info},
                                {"IOPS_Total": read_write},
                                {"BW": randread_randwrite},
                            ]
                        }
                    ]

                elif runtype["runtype"] == "randwrite":
                    write_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, write)
                    ).output.split()
                    writebw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'"
                        % (iostat, sdisk, randwrite)
                    ).output.split()
                    iostat_dict[sdisk] = [
                        {"测试4": [{"IOPS": write_info}, {"BW": writebw_info}]}
                    ]

                elif runtype["runtype"] == "randread":
                    read_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, read)
                    ).output.split()
                    readbw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, randread)
                    ).output.split()
                    iostat_dict[sdisk] = [
                        {"测试5": [{"IOPS": read_info}, {"BW": readbw_info}]}
                    ]

                elif runtype["runtype"] == "randmix_readwrite":
                    write_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, write)
                    ).output.split()
                    read_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, read)
                    ).output.split()
                    writebw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'"
                        % (iostat, sdisk, randwrite)
                    ).output.split()
                    readbw_info = command(
                        "cat %s |grep %s |awk '{print $%s}'" % (iostat, sdisk, randread)
                    ).output.split()

                    read_write = [
                        float(x) + float(y) for x, y in zip(read_info, write_info)
                    ]
                    randread_randwrite = [
                        float(x) + float(y) for x, y in zip(writebw_info, readbw_info)
                    ]
                    iostat_dict[sdisk] = [
                        {
                            "测试6": [
                                {"IOPS_R": read_info},
                                {"IOPS_W": write_info},
                                {"IOPS_Total": read_write},
                                {"BW": randread_randwrite},
                            ]
                        }
                    ]
        return iostat_dict


if __name__ == "__main__":
    # create reports dir
    draw_info = []
    make_dir(reports_path)
    time.sleep(1)
    make_dir(f"{reports_path}system_logs")
    if alone:
        runtypelist = [alone]
    else:
        runtpyelist = [write, read, mix_readwrite, randwrite, randread, randmix_readwrite]
    for runtype in runtypelist:
        disks = dev
        run = runtype["runtype"]
        set_job = runtype["jobs"]
        set_bs = runtype["bs"]
        set_qdepth = runtype["qdepth"]

        if set_job:
            numjobs = "--numjobs=" + set_job
        else:
            numjobs = ""

        if set_bs:
            # if ';' in bs:
            bs = "--bs=" + set_bs
        else:
            bs = ""

        if set_qdepth:
            qdepth = "--iodepth=" + set_qdepth
        else:
            qdepth = ""

        savelog(info="===== autotest is running =====")

        # get disk list
        if disks == "all":
            disk_list = command(
                "fdisk -l | grep -iPo 'Disk /dev/\w+*' | awk '{print $2}'"
            ).output.split()
            os_dev = command(
                "df | grep -i /boot | awk '{print $1}' | grep -Eo '/dev/sd[a-z]+'  | head -n1"
            ).output
            disk_list.remove(os_dev)
        else:
            if ";" in disks:
                disk_list = [i.split()[0] for i in disks.split(";")]
            else:
                disk_list = disks.split()

        # create dev dir
        for dev in disk_list:
            sdisk = dev.split("/")[-1]
            dev_path = f"{reports_path}{sdisk}/"
            make_dir(dev_path, True)
            if disktype == "sata":
                command(
                    f"hdparm --user-master m --security-set-pass NULL {dev} ; hdparm --user-master m --security-erase NULL {dev} "
                )
            elif disktype == "nvme":
                command(f"nvme format -s 1 {dev}")
            elif disktype == "sas":
                command(f"sg_format --format {dev}")

        check_smart(disk_list)

        log_parser_path = (
            f"{os.path.dirname(workpath)}/common_test/log-parser/log_parser.py"
        )
        command(f"python3 {log_parser_path} -b ")
        print("run log_parser_path.py -b  ")
        save_lsscsl()
        save_smart(disk_list, disktype)
        #' 'write', 'read', 'mix_readwrite', 'randwrite','randread', 'randmix_readwrite']

        for dev in disk_list:
            if task:
                task_id = task_list[dev]
                print(task_id)
                set_task = f"taskset -c {task_id} "
                print(set_task)
            else:
                set_task = ""

            pid_list = []
            dev_report = dev.split("/")[2]
            print(dev_report)
            if run == "write":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth} --direct=1 --sync=0 "
                    f"--ioengine=libaio --rw={run} {bs} {numjobs} {qdepth} "
                    f"--filename={dev} --ramp_time=60 --runtime=36000 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}.log --write_bw_log={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_bw.log "
                    f"--write_iops_log={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_iops.log --write_lat_log={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_lat.log --output-format=json"
                )
            if run == "read":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth} --direct=1 --sync=0 "
                    f"--ioengine=libaio --rw={run} {bs} {numjobs} {qdepth} "
                    f"--filename={dev} --ramp_time=60 --runtime=25200 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}.log --write_bw_log={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_bw.log "
                    f"--write_iops_log={reports_path}{dev}/{reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_iops.log --write_lat_log={reports_path}{dev_report}/perf_seq_{run}_{set_bs}_{set_job}_{set_qdepth}_lat.log --output-format=json"
                )
            if run == "mix_readwrite":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/preconfig_rand_write_{set_bs}_{set_job}_{set_qdepth} --direct=1 --sync=0 "
                    f"--ioengine=libaio --rw={run} {bs} {numjobs} {qdepth} --rwmixread=70 "
                    f"--filename={dev} --ramp_time=0 --runtime=25200 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output=perf_{reports_path}{dev_report}/preconfig_rand_write_{set_bs}_{set_job}_{set_qdepth}.log --output-format=json"
                )
            if run == "randwrite":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/perf_rand_write_{set_bs}_{set_job}_{set_qdepth} --direct=1 "
                    f"--ioengine=libaio --rw={run} {bs} {numjobs} {qdepth} "
                    f"--filename={dev} --ramp_time=60 --runtime=36000 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output={reports_path}{dev_report}/perf_rand_write_{set_bs}_{set_job}_{set_qdepth}.log --write_bw_log={reports_path}{dev_report}/perf_rand_write_{set_bs}_{set_job}_{set_qdepth}_bw.log "
                    f"--write_iops_log={reports_path}{dev_report}/perf_rand_write_{set_bs}_{set_job}_{set_qdepth}_iops.log --write_lat_log={reports_path}{dev_report}/perf_rand_write_{set_bs}_{set_job}_{set_qdepth}_lat.log --output-format=json"
                )
            if run == "randread":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/perf_rand_read_{set_bs}_{set_job}_{set_qdepth} --direct=1 --sync=0 "
                    f"--ioengine=libaio --rw={run} {bs} {numjobs} {qdepth} "
                    f"--filename={dev} --ramp_time=60 --runtime=25200 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output={reports_path}{dev_report}/perf_rand_read_{set_bs}_{set_job}_{set_qdepth}.log --write_bw_log={reports_path}{dev_report}/perf_rand_read_{set_bs}_{set_job}_{set_qdepth}_bw.log "
                    f"--write_iops_log={reports_path}{dev_report}/perf_rand_read_{set_bs}_{set_job}_{set_qdepth}_iops.log --write_lat_log={reports_path}{dev_report}/perf_rand_read_{set_bs}_{set_job}_{set_qdepth}_lat.log --output-format=json"
                )
            if run == "randmix_readwrite":
                pid = nohup(
                    f"{set_task}fio --name={reports_path}{dev_report}/perf_rand_mixrw_{set_bs}_{set_job}_{set_qdepth} --direct=1 --sync=0 "
                    f"--ioengine=libaio --rw={run} {bs} --rwmixread=70 {numjobs} {qdepth} "
                    f"--filename={dev} --ramp_time=60 --runtime=25200 --time_based "
                    f"--randrepeat=0 --norandommap --log_avg_msec=1000 --group_reporting "
                    f"--output={reports_path}{dev_report}/perf_rand_mixrw_{set_bs}_{set_job}_{set_qdepth}.log --write_bw_log={reports_path}{dev_report}/perf_rand_mixrw_{set_bs}_{set_job}_{set_qdepth}_bw.log "
                    f"--write_iops_log={reports_path}{dev_report}/perf_rand_mixrw_{set_bs}_{set_job}_{set_qdepth}_iops.log --write_lat_log={reports_path}{dev_report}/perf_rand_mixrw_{set_bs}_{set_job}_{set_qdepth}_lat.log --output-format=json"
                )
            print(f"fio {dev} {run} {set_bs} {set_job} {set_qdepth} is run ")
            pid_list.append(pid)

        iostat_pids, iostat_log_list = get_iostat_log(disk_list, set_bs, run)
        get_speed_object = multiprocessing.Pool(len(disk_list))
        get_temp_object = multiprocessing.Pool(len(disk_list))

        for dev in disk_list:
            sdisk = dev.split("/")[-1]
            get_temp_object.apply_async(
                func=get_temp_log,
                args=(
                    disktype,
                    sdisk,
                    set_bs,
                    run,
                ),
            )
            get_speed_object.apply_async(
                func=get_speed,
                args=(
                    disktype,
                    sdisk,
                    set_bs,
                    run,
                ),
            )

        time.sleep(20)
        for pid in pid_list:
            wait_process(pid)

        get_speed_object.terminate()
        get_temp_object.terminate()

        for pid in iostat_pids:
            kill_process(pid)

        # draw iostat info
        iostat_dict = draw_iostat_info(iostat_log_list, disk_list)
        draw_info.append(iostat_dict)

        # draw temp
        draw_temp_info(disk_list, disktype, set_bs, run)

        # draw speed  'LnkCap', 'LnkSta', 'LnkCtl2'
        draw_speed_info(disk_list, set_bs, run)

        time.sleep(3)
        save_smart(disk_list, disktype, "after")
        command(f"rm -rf  {os.path.dirname(workpath)}/common_test/log-parser/*.log ")
        command(f"python3 {log_parser_path} -a ")
        print("run log_parser_path.py -a ")
        time.sleep(5)
        command(
            f"cp -r {os.path.dirname(workpath)}/common_test/log-parser/reports/ {reports_path}system_logs/{run}_{set_bs}_{set_job}_{set_qdepth}"
        )
        # command(f"mv  {os.path.dirname(workpath)}/common_test/log-parser/*.log {reports_path}system_logs/{run}_{set_bs}_{set_job}_{set_qdepth}")
        time.sleep(5)
    # print(draw_info)
    test = ReportHelper(
        log_path=f"{reports_path}/",
        rpt_path=f"{reports_path}/rpt3.xlsx",
        iostat_data=draw_info,
    )
    test.generate_report()

    print("=" * 53)
    print("=" * 20 + "test is finsh" + "=" * 20)
