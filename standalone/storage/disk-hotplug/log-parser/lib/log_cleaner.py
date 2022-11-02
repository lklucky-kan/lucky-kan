#!/usr/bin/python3
'''
description:this script is used for legacy scripts logs clean and backup
            default log dir must be 'reports' under the legacy scripts dir.
            default backup path is bk_logs outside of tea
author: houyuhan
'''

import argparse
import re, os
import shutil
from datetime import datetime


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='this script is used for legacy scripts logs clean and backup.')
    parser.add_argument('-t','--target', required=True, help='the target script dir name of logs needed to clean or backup, the logs dir name must be "reports" under the script dir')
    parser.add_argument('-c','--clean', action='store_true', help='clean the target logs, sample: python3 log_cleaner.py --clean')
    parser.add_argument('-b','--backup',nargs='?', action='store', help='backup path of the logs, default will be bk_logs outside of tea dir, sample:  python3 log_cleaner.py --backup')
    
    args = parser.parse_args()

    cur_path = os.path.abspath('.')
    standalone_path = ''

    match = re.search(r'(\S+standalone)', cur_path)
    if match:
        standalone_path= match.group(1)

    target_path = os.path.join(standalone_path,args.target, 'reports')

    if args.clean:
        shutil.rmtree(target_path)
        print(target_path + ' is cleaned!') 
    else:
        bk_path = args.backup

        if bk_path == None:
            match = re.search(r'(\S+)tea', cur_path)
            if match:
                bk_path = os.path.join(match.group(1),'bk_logs', args.target, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

        print(bk_path)

        # if not os.path.exists(bk_path):
        #     os.makedirs(bk_path)

        shutil.copytree(target_path, bk_path)
        print('backup ' + target_path + ' to ' + bk_path)

        shutil.rmtree(target_path)
        print('removed ' + target_path)
