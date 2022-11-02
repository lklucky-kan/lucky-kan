#/usr/bin/python

import re, os, sys, time, shutil, platform
from os import popen, system
from json import dumps
from argparse import ArgumentParser, RawTextHelpFormatter
tea_path = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        os.pardir
    )
)
sys.path.append(tea_path)
sys.path.append(
    os.path.join(tea_path, 'lib')
)
from lib.ResultParseTerse import *
from common.communication.local import Local
from common.other.log import Logger, Log_Manage




class StorageFio():
    '''
    this is used for storage fio test.
    author: Kail
    '''

    def filter_info(self, date):

        rst = re.findall('sd.', date, re.I)
        if rst:
            return rst[0]

        rst = re.findall('nvme\w+n', date, re.I)
        if rst:
            return rst[0]


    def get_server_binfo(self, dlist):
        '''
        description: get server info before run fio
        author: Kail
        params: dlist, the test disk list
        '''

        get_info_list = [
            'dmidecode | grep "System Information" -A9 | egrep "Manufacturer|Product|Serial" > {0}/server_info.log',
            'lscpu > {0}/cpu_info.log',
            'dmidecode -t memory > {0}/memory_info.log',
            'uname -a > {0}/os_info.log',
            'lsscsi > {0}/lsscsi_info.log',
            'smartctl -a {1} > {0}/smart_info_before.log'
        ]
        for d in dlist:
            sdisk = d.split('/')[-1]
            dev_logpath = rep_path + sdisk
            iostat_path = self.join_path(dev_logpath, 'iostat')
            # clean dev reports
            [ os.mkdir(p) for p in [dev_logpath, iostat_path] if not os.path.isdir(p) ]
            #for cmd in get_info_list:
            local_os.cmd(
                get_info_list[-1].format(dev_logpath, d)
            )
        for cmd in get_info_list[:-1]:
            local_os.cmd(cmd.format(before_logpath))

    def join_path(self, path, fp):
        '''
        description: join two path or join path and file
        author: Kail
        params: path: raw path
                fp: file or path
        return: np, new real path
        '''
        return os.path.realpath(
            os.path.join(path, fp)
        )

    def fio_para(self, dt, rt, st):
        '''
        description: define fio para
        author: Kail
        params: dt: the disk type, choices: [nvme/ssd/hdd]
                rt: the run type, choices: [perf/stress]
                st: the sequence type, choices: [seq/random]
        return: bs_list, job_list, qd_list
        '''
        if disktype == 'nvme':
            if runtype == 'stress':
                bs_list = [4, 128]
                job_list = [1]
                qd_list = [1, 128]
            elif runtype == 'perf':
                if seqtype == 'seq':
                    bs_list = [1024, 512, 256, 128, 64, 32, 16, 8, 4]
                    job_list = [1]
                    qd_list = [1, 8, 32, 128]
                elif seqtype == 'random':
                    bs_list = [4, 8, 16, 32]
                    job_list = [1, 4, 8]
                    qd_list = [1, 8, 32, 64, 128]
        elif disktype == 'ssd':
            if runtype == 'stress':
                bs_list = [4, 128]
                job_list = [1]
                qd_list = [1, 32]
            elif runtype == 'perf':
                if seqtype == 'seq':
                    bs_list = [1024, 512, 256, 128, 64, 32, 16, 8, 4]
                    job_list = [1]
                    qd_list = [1, 32]
                elif seqtype == 'random':
                    bs_list = [4, 8, 16, 32]
                    job_list = [1, 4]
                    qd_list = [1, 32]
        elif disktype == 'hdd':
            if runtype == 'stress':
                bs_list = [4, 1024]
                job_list = [1]
                qd_list = [32]
            elif runtype == 'perf':
                if seqtype == 'seq':
                    bs_list = [1024, 512, 256, 128]
                    job_list = [1]
                    qd_list = [1, 32]
                elif seqtype == 'random':
                    bs_list = [4, 8, 16, 64]
                    job_list = [1]
                    qd_list = [1, 32]

        if seqtype == 'seq':
            rw_dict = {
                'read': 'read',
                'write': 'write',
                'rw': 'rw'
            }
        else:
            rw_dict = {
                'read': 'randread',
                'write': 'randwrite',
                'rw': 'randrw'
            }
        return bs_list, job_list, qd_list, rw_dict

    def fio_read(self):
        # [Random/Seq] Read Test
        logger.info('Starting %s read test...' %seqtype)
        log_list = []
        for bs in bs_list:
            for job in job_list:
                for qd in qd_list:
                    logger.info('Start blocksize: {0}, numjobs: {1}, iodepth: {2} {3} read...'.format(bs, job, qd, seqtype))
                    for disk in fd_list:
                        sdisk = disk.split('/')[-1]
                        dev_logpath = rep_path + sdisk
                        iostat_path = self.join_path(dev_logpath, 'iostat')
                        iostat_disk = self.filter_info(sdisk)
                        if os_disk in sdisk:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(os_disk, bs, rw_dict['read'], iostat_path, job, qd)
                            )
                        else:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(iostat_disk, bs, rw_dict['read'], iostat_path, job, qd)
                            )
                        job_name="{0}kb_{1}_RD_{2}job_{3}qd".format(bs, seqtype, job, qd, sdisk)
                        log = dev_logpath + '/' + sdisk + '_' + seqtype + '_read_data.log'
                        io_log = dev_logpath + '/' + sdisk + '_' + job_name
                        log_list.append(log)
                        logger.info('start disk {0} {1} read test'.format(sdisk, seqtype))
                        if tset:
                            ts_para = 'taskset -c %s ' %core_dict['/dev/' + sdisk]
                        else:
                            ts_para = ''
                        if seqtype == 'random':
                            rand_para = '--norandommap=1 --randrepeat=0 --iopsavgtime=1000 --write_iops_log'
                        else:
                            rand_para = '--bwavgtime=1000 --write_bw_log'
                        cmd = "{7}fio --name={0} --filename=/dev/{5} --ioengine=libaio " +\
                            "--direct=1 --thread=1 --numjobs={1} --iodepth={2} " +\
                            "--rw={8} --bs={3}k --runtime={4} --time_based=1 --size=100% " +\
                            "--group_reporting --log_avg_msec=1000 " +\
                            "{9}={10} --minimal >> {6} &"
                        local_os.bk_cmd(
                            cmd.format(
                                job_name, job, qd, bs,
                                fiotime, sdisk, log, ts_para,
                                rw_dict['read'], rand_para, io_log
                            )
                        )
                    storage_test.wait_process('fio')
                    popen('killall iostat')
                    logger.info('{0}bs_{1}job_{2}io {3} read test finish'.format(bs, job, qd, seqtype))

        log_list = list(set(log_list))
        for log in log_list:
            logger.info('start parse log %s' %log)
            try:
                parseData(
                    infile=log,
                    outfile=log.replace('.log', '.csv'),
                    rwm='p',
                    iops=iops_tp,
                    logger=logger
                )
            except:
                logger.info('parse log %s fail' %log)


    def fio_write(self):
        # [Random/Seq] Write Test
        logger.info('Starting %s write test...' %seqtype)
        log_list = []
        for bs in bs_list:
            for job in job_list:
                for qd in qd_list:
                    logger.info('Start blocksize: {0}, numjobs: {1}, iodepth: {2} {3} write...'.format(bs, job, qd, seqtype))
                    for disk in fd_list:
                        sdisk = disk.split('/')[-1]
                        dev_logpath = rep_path + sdisk
                        iostat_path = self.join_path(dev_logpath, 'iostat')
                        iostat_disk = self.filter_info(sdisk)
                        if os_disk in sdisk:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(os_disk, bs, rw_dict['write'], iostat_path, job, qd)
                            )
                        else:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(iostat_disk, bs, rw_dict['write'], iostat_path, job, qd)
                            )
                        job_name='{0}kb_{1}_WR_{2}job_{3}qd'.format(bs, seqtype, job, qd, sdisk)
                        log = dev_logpath + '/' + sdisk + '_' + seqtype + '_write_data.log'
                        io_log = dev_logpath + '/' + sdisk + '_' + job_name
                        log_list.append(log)
                        logger.info('start disk {0} {1} write test'.format(sdisk, seqtype))
                        if tset:
                            ts_para = 'taskset -c %s ' %core_dict['/dev/' + sdisk]
                        else:
                            ts_para = ''
                        if seqtype == 'random':
                            rand_para = '--norandommap=1 --randrepeat=0 --iopsavgtime=1000 --write_iops_log'
                        else:
                            rand_para = '--bwavgtime=1000 --write_bw_log'
                        cmd = "{7}fio --name={0} --filename=/dev/{5} --ioengine=libaio " +\
                            "--direct=1 --thread=1 --numjobs={1} --iodepth={2} " +\
                            "--rw={8} --bs={3}k --runtime={4} --time_based=1 --size=100% " +\
                            "--group_reporting --log_avg_msec=1000 " +\
                            "{9}={11} --minimal >> {6} &"
                        local_os.bk_cmd(
                            cmd.format(
                                job_name, job, qd, bs, fiotime,
                                sdisk, log, ts_para,
                                rw_dict['write'], rand_para,
                                dev_logpath, io_log
                            )
                        )
                    storage_test.wait_process('fio')
                    popen('killall iostat')

                    logger.info('{0}bs_{1}job_{2}io {3} write test finish'.format(bs, job, qd, seqtype))

        log_list = list(set(log_list))
        for log in log_list:
            logger.info('start parse log %s' %log)
            try:
                parseData(
                    infile=log,
                    outfile=log.replace('.log', '.csv'),
                    rwm='p',
                    iops=iops_tp,
                    logger=logger
                )
            except:
                logger.info('parse log %s fail' %log)

    def fio_mix(self):
        # [Random/Seq] mix R70 W30 test
        logger.info('Starting %s mix rw test...' %seqtype)
        log_list = []
        for bs in bs_list:
            for job in job_list:
                for qd in qd_list:
                    logger.info(
                        'Start blocksize: {0}, numjobs: {1}, iodepth: {2} {3} mix rw test...'\
                        .format(bs, job, qd, seqtype)
                    )
                    for disk in fd_list:
                        sdisk = disk.split('/')[-1]
                        dev_logpath = rep_path + sdisk
                        iostat_path = self.join_path(dev_logpath, 'iostat')
                        iostat_disk = self.filter_info(sdisk)
                        if os_disk in sdisk:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(os_disk, bs, rw_dict['rw'], iostat_path, job, qd)
                            )
                        else:
                            local_os.bk_cmd(
                                'iostat -xm 1 |grep {0} >> {3}/{0}_{1}kb_{4}job_{5}qd_{2}_iostat.log &'\
                                .format(iostat_disk, bs, rw_dict['rw'], iostat_path, job, qd)
                            )
                        job_name="{0}kb_{1}_mix_70-30_{2}job_{3}qd".format(bs, seqtype, job, qd, sdisk)
                        log = dev_logpath + '/' + sdisk + '_' + seqtype + '_mix70-30_data.log'
                        io_log = dev_logpath + '/' + sdisk + '_' + job_name
                        log_list.append(log)
                        logger.info('start disk {0} {1} mix rw test'.format(sdisk, seqtype))
                        if tset:
                            ts_para = 'taskset -c %s ' %core_dict['/dev/' + sdisk]
                        else:
                            ts_para = ''
                        if seqtype == 'random':
                            rand_para = '--norandommap=1 --randrepeat=0 --iopsavgtime=1000 --write_iops_log'
                        else:
                            rand_para = '--bwavgtime=1000 --write_bw_log'
                        cmd = "{7}fio --name={0} --filename=/dev/{5} --ioengine=libaio " +\
                            "--direct=1 --thread=1 --numjobs={1} --iodepth={2} " +\
                            "--rw={8} --bs={3}k --rwmixread=70 --runtime={4} --time_based=1 --size=100% " +\
                            "--group_reporting --log_avg_msec=1000 " +\
                            "{9}={11} --minimal >> {6} &"
                        local_os.bk_cmd(
                            cmd.format(
                                job_name, job, qd,
                                bs, fiotime, sdisk,
                                log, ts_para, rw_dict['rw'],
                                rand_para, dev_logpath, io_log
                            )
                        )
                    storage_test.wait_process('fio')
                    popen('killall iostat')
                    logger.info('{0}bs_{1}job_{2}io {3} mix rw test finish'.format(bs, job, qd, seqtype))

        log_list = list(set(log_list))
        for log in log_list:
            logger.info('start parse log %s' %log)
            try:
                parseData(
                    infile=log,
                    outfile=log.replace('.log', '.csv'),
                    rwm='mix',
                    iops=iops_tp,
                    logger=logger
                )
            except:
                logger.info('parse log %s fail' %log)

    def wait_process(self, task, timeout=0):
        waittime = 0
        while True:
            process = os.popen('ps -ax | grep -i " %s" | grep -v grep' %task).read()
            if process:
                time.sleep(1)
                waittime += 1
                if timeout and waittime >= timeout:
                    logger.error('after %s second, task %s still exist' %(timeout, task))
                    raise Exception('after %s second, task %s still exist' %(timeout, task))
            else:
                break

def clean_paths(*paths):
    for path in paths:
        if type(path) is list or type(path) is tuple:
            for p in path:
                if os.path.exists(p):
                    shutil.rmtree(p)
                os.makedirs(p)
        else:
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)

def get_cpuinfo():
    cpu_dict = {}
    cpu_power = os.popen('cpupower monitor').read().strip().splitlines()
    if 'euleros' in platform.platform() and 'PKG|CORE' not in cpu_power[1]:
        for line in cpu_power[1:]:
            if re.search(r'\s+CPU\|\s+C', line):
                cpu = line.split('|')[1].strip().lstrip('C')
                cpu_dict['cpu' + cpu] = []
            else:
                core = line.split('|')[0].strip()
                cpu_dict['cpu' + cpu].append(core)
    else:
        for line in cpu_power[2:]:
            cpu = line.split('|')[0].strip()
            core = int(line.split('|')[2].strip())
            if 'cpu' + cpu not in cpu_dict:
                cpu_dict['cpu' + cpu] = []
            cpu_dict['cpu' + cpu].append(core)
    return cpu_dict



if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser(description='Run fio on storage',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-bs',
                        dest='blocksize', type=str,
                        help='define the fio "--bs" para')
    parser.add_argument('-job',
                        dest='numjobs', type=str,
                        help='define the fio "--numjobs" para')
    parser.add_argument('-d',
                        dest='dev', type=str,
                        required = True,
                        help='define the disks list, when test all disks, use "-d all"')
    parser.add_argument('-t',
                        dest='time', type=int,
                        required = True,
                        help='define the fio runtime')
    parser.add_argument('-qd',
                        dest='queuedepth', type=str,
                        help='define the fio "iodepth" para')
    parser.add_argument('-st',
                        dest='seqtype', type=str,
                        required = True,
                        choices = ['seq', 'random'],
                        help='define the fio run sequence type')
    parser.add_argument('-dt',
                        dest='disktype', type=str,
                        required = True,
                        choices = ['hdd', 'ssd', 'nvme'],
                        help='define the disk type')
    parser.add_argument('-rt',
                        dest='runtype', type=str,
                        required = True,
                        choices = ['perf', 'stress'],
                        help='define the disk type')
    parser.add_argument('-ts', '--taskset',
                        dest='taskset',
                        action='store_true',
                        help='run cpu taskset')
    parser.add_argument('-pre', '--precondition',
                        type=str,
                        choices = ['only', 'no'],
                        help="choose if doing fio precondition, do precondition when without this para:\n" +
                             "    -pre only    :only doing precondition but not doing read/write test\n" +
                             "    -pre no      :only doing read/write test but not doing precondition"
    )
    parser.add_argument('-rw_seq', '--rwseq',
                        type=str,
                        help="choose which read/write/mix seq mode to do eg:,\n" +
                             "-rw_seq read\n" +
                             "-rw_seq 'read write'\n" +
                             "-rw_seq 'read write mix'"
    )
    parser.add_argument('-cl', dest='clear_old',
                        type=str,
                        choices = ['y', 'Y', 'n', 'N'],
                        help="if clear the old reports :,\n" +
                             "y, Y     clear the old reports\n" +
                             "n, N     not clear the old reports\n"
    )





    group1 = parser.add_argument_group('Run SSD random stress test, fio runtime 7200',
                                       'python %(prog)s ' +
                                       r" -t 7200 -d '/dev/sdb /dev/sdc' -st random -dt ssd -rt stress"
    )
    group2 = parser.add_argument_group('Run NVME seq perf test, fio runtime 600',
                                       'python %(prog)s ' +
                                       r" -t 600 -d '/dev/nvme0n1 /dev/nvme1n1' -st seq -dt nvme -rt perf"
    )
    group3 = parser.add_argument_group('Run NVME seq perf test, fio runtime 600, ' +
                                       'nvme0n1 taskset CPU0 cores, nvme1n1 taskset CPU1 cores',
                                       'python %(prog)s ' +
                                       r" -t 600 -d '/dev/nvme0n1;/dev/nvme1n1' -st seq -dt nvme -rt perf -ts"
    )
    group4 = parser.add_argument_group('Run NVME seq perf test, fio runtime 600, ' +
                                       'nvme0n1 nvme1n1 random bind CPU cores',
                                       'python %(prog)s ' +
                                       r" -t 3000 -d '/dev/nvme0n1 /dev/nvme1n1' -st seq -dt nvme -rt perf -ts"
    )



    args = parser.parse_args()
    blocksize = args.blocksize
    job = args.numjobs
    disks = args.dev
    fiotime = args.time
    qdepth = args.queuedepth
    seqtype = args.seqtype
    disktype = args.disktype
    runtype = args.runtype
    tset = args.taskset
    pretest = args.precondition
    rw_seq = args.rwseq
    clr_old = args.clear_old


    # chdir to 'tea' path
    cur_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
    os.chdir(cur_path)

    rep_path = cur_path + '/reports/'
    before_logpath = rep_path + 'before'
    log_file = "storage_fio"
    logger = Logger(log_file=log_file)
    local_os = Local(logger=logger)

    #clean paths
    if not os.path.isdir(rep_path): os.mkdir(rep_path)
    Log_Manage(logger=logger).clear_log(rep_path, clr_old)
    if not os.path.isdir(before_logpath): os.mkdir(before_logpath)

    # parse the argument
    if seqtype == 'seq':
        iops_tp = 'bw'
    elif seqtype == 'random':
        iops_tp = 'iops'

    os_disk = local_os.cmd("df | grep -i /boot | awk '{print $1}' | grep -Eo '/dev/sd[a-z]+'  | head -n1" )#
    if isinstance(os_disk, list):
        os_disk=os_disk[0]
    #os_disk = '/dev/' + ''.join(os_disk)
    if disks == 'all':
        disk_list = local_os.cmd(" fdisk -l | grep -iPo 'Disk /dev/sd\w+|Disk /dev/nvme\w+' | awk '{print $2}'")
    else:
        if ';' in disks:
            disk_list = [i.split() for i in disks.split(';')]
        else:
            disk_list = disks.split()
    if os_disk in disk_list:
        disk_list.remove(os_disk)
    else:
        if len(disk_list) == 2 and type(disk_list[0]) is list:
            for dl in disk_list:
                if os_disk in dl:
                    dl.remove(os_disk)

    print('disk_list')
    print(disk_list)
    print('os_disk')
    print(os_disk)
    

    if len(disk_list) == 0:
        logger.info('These is only os disk exist, fio cannot run in OS disk')
        raise SystemExit()

    storage_test = StorageFio()
    if len(disk_list) == 2 and type(disk_list[0]) is list:
        fd_list = [ d for lis in disk_list for d in lis ]
    else:
        fd_list = disk_list
    storage_test.get_server_binfo(fd_list)

    # define fio pare
    bs_list, job_list, qd_list, rw_dict = storage_test.fio_para(disktype, runtype, seqtype)
    if blocksize:
        bs_list = [ int(i) for i in blocksize.split() ]
    if job:
        job_list = [ int(i) for i in job.split() ]
    if qdepth:
        qd_list = [ int(i) for i in qdepth.split() ]
    # devs_para = [ d.split('/')[-1] for d in disk_list ]

    # calculat cores in per hdd
    if tset:
        cpu_dict = get_cpuinfo()
        cores_list = [ int(c) for v in cpu_dict.values() for c in v ]
        cores_list.sort()
        cpu_num = len(cores_list)
        if len(disk_list) == 2 and type(disk_list[0]) is list:
            disk_num = len([i for li in disk_list for i in li])
        else:
            disk_num = len(disk_list)
        max_disk_cores = int(cpu_num / disk_num)
        max_job = max(job_list)
        if max_job < max_disk_cores:
            max_disk_cores = max_job
        elif max_job == max_disk_cores:
            max_disk_cores = max_disk_cores - 1
        elif max_job > max_disk_cores:
            if 4 < max_disk_cores < 8:
                max_disk_cores = 4
            elif max_disk_cores == 4:
                max_disk_cores = 3

        core_dict = {}
        if len(disk_list) == 2 and type(disk_list[0]) is list and len(cpu_dict) == 2:
            for d in disk_list[0]:
                core_dict[d] = []
                for n in range(max_disk_cores):
                    core_dict[d].append(cpu_dict['cpu0'].pop(2))
            for d in disk_list[1]:
                core_dict[d] = []
                for n in range(max_disk_cores):
                    core_dict[d].append(cpu_dict['cpu1'].pop(0))
        else:
            if type(disk_list[0]) is list and len(cpu_dict) != 2:
                disk_list = [ i for l in disk_list for i in l ]
            # cores_list = list(range(1, cpu_num))
            for d in disk_list:
                core_dict[d] = []
                for n in range(max_disk_cores):
                    core_dict[d].append(cores_list.pop(2))
        for k, v in core_dict.items():
            core_dict[k] = ','.join([ str(i) for i in v ])
        logger.info('\n' +
                'disk: ' + str(disk_list) + '\n' +
                'job: ' + str(job_list) + '\n' +
                'disk cores: ' + str(dumps(core_dict, indent=4))
        )


    if pretest == 'no':
        pass
    else:
        # [Random/Seq] Write Precondition
        logger.info('Starting write precondition...')
        if disktype in ['ssd', 'nvme']:
            for d in fd_list:
                sdisk = d.split('/')[-1]
                dev_logpath = rep_path + sdisk
                logger.info('start disk {0} seq write precondition test'.format(sdisk))
                if runtype == 'perf':
                    bs_para = '--bs=128k --loops=3 '
                else:
                    bs_para = '--bs=128k --runtime=2h --time_based=1 '
                cmd = "fio --ioengine=libaio --name=Precondition_{1} --filename=/dev/{1} " +\
                    "--direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=write " +\
                    "--size=100% {2}--group_reporting --log_avg_msec=1000 " +\
                    "--bwavgtime=1000 --write_bw_log={0}/{1}_seq_wr_precondition >> {0}/{1}_seq_write_precondition.log &"
                local_os.bk_cmd(cmd.format(dev_logpath, sdisk, bs_para))
            storage_test.wait_process('fio')
            logger.info('seq write precondition finish')

            if seqtype == 'random':
                for d in fd_list:
                    sdisk = d.split('/')[-1]
                    dev_logpath = rep_path + sdisk
                    logger.info('start disk {0} random write precondition test'.format(sdisk))
                    cmd = "fio --ioengine=libaio --name=Precondition_{1} --filename=/dev/{1} " +\
                        "--direct=1 --thread=1 --numjobs=1 --iodepth=128 --rw=randwrite --bs=4k " +\
                        "--runtime=8h --time_based=1 --size=100% --norandommap=1 --randrepeat=0 " +\
                        "--group_reporting --log_avg_msec=1000 --iopsavgtime=1000 " +\
                        "--write_iops_log={0}/{1}_random_wr_precondition>> {0}/{1}_random_write_precondition.log &"
                    local_os.bk_cmd(cmd.format(dev_logpath, sdisk))
                storage_test.wait_process('fio')
                logger.info('random write precondition finish')
        if pretest == 'only':
            sys.exit()

    rwm_dict = {
        'read': 'storage_test.fio_read()',
        'write': 'storage_test.fio_write()',
        'mix': 'storage_test.fio_mix()'
    }
    if rw_seq:
        rw_list = rw_seq.split()
    else:
        rw_list = ['write', 'read', 'mix']
    for m in rw_list:
        eval(rwm_dict[m])

    #python ResultParseTerse.py -t p -i iops -f "$DEV"_random_write_data.log -r "$DEV"_random_write_data_op.csv
    #    parseData(infile=, outfile, rwm, iops)
    #    # [Random/Seq] Read Precondition
    #    if seqtype == 'random':
    #        for d in fd_list:
    #            sdisk = d.split('/')[-1]
    #            dev_logpath = rep_path + sdisk
    #            print("fio --ioengine=libaio --name=pre_{1} --filename=/dev/{1}\
    #                --direct=1 --thread=1 --numjobs=1 --iodepth=1 --rw=randread --bs=4k \
    #                --runtime=1800 --time_based=1 --size=100% --norandommap=1 --randrepeat=0 \
    #                --group_reporting \
    #                > {0}/{1}_{2}_read_precondition.log &" \
    #                .format(dev_logpath, sdisk, seqtype)
    #            )
    #        storage_test.wait_process('fio')


    for disk in fd_list:
        after_cmd = 'smartctl -a /dev/{1} > {0}{1}/smart_info_after.log'.format(rep_path, disk.split('/')[-1])
        local_os.cmd(after_cmd)
