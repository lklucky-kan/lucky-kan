# 执行mudan_disk_fio.py 之前确认Python包是否安装成功
# pip3 install matplotlib openpyxl
# 确保 fio 已经装上 yum install fio

disktype = "hdd"  # define the disk type
ramp_time = "0"  # define the runtime eg:0
dev = "all"  # define the disks list eg "/dev/sdb;/dev/sdc", when test all disks, use "-d all"
task = False  # Is add task parameter？

task_list = {
    "/dev/sdb": "1-2",  # define the task
    "/dev/nvme0n2": "3-4",  # define the task
}

read = {
    "runtype": "read",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}

write = {
    "runtype": "write",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}

randread = {
    "runtype": "randread",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}

randwrite = {
    "runtype": "randwrite",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}

mix_readwrite = {
    "runtype": "mix_readwrite",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}

randmix_readwrite = {
    "runtype": "randmix_readwrite",
    "jobs": "1",  # define the numjobs eg: 1 or 2 ...
    "bs": "8k",  # define the BS eg: 1k;8k;..1M
    "qdepth": "32",  # define the Qdepth eg:32
}
alone = False # 单独跑某一个模式 ， 直接加参数 不需要加引号 eg：mix_readwrite
