import argparse
import os
import re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='original log parser.')
    parser.add_argument('-p', '--path', required=True, help='-p log_path')
    args = parser.parse_args()

    log_path = args.path

    if not os.path.exists(log_path):
        pass #implement in future

    else:
        result = 'pass'
        reason = ''
        test_done = False
        with open(log_path, 'r') as f:
            for line in f:
                #NO. 1 2021-05-19_10:10:38 sdr check Failed
                match = re.search(r'(NO\.\s*\d+)\s+\S+\s+(.*check failed)', line, re.I)
                if match:
                    result = 'fail'
                    if match.group(2) not in reason:
                        reason += match.group(1) + ' ' + match.group(2) + ';'
                else:
                    #2 cycles warm reboot test finished.
                    match = re.search(r'test finished', line, re.I)
                    if match:
                        test_done = True

        
        print('result:' + result)
        print('reason:' + reason)
        
        if test_done:
            print('test done')





