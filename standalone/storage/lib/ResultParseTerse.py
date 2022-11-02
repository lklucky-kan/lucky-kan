#!/usr/bin/python

import argparse
import re
import os



def parseData(infile, outfile, rwm, iops, **kwargs):
    if kwargs.get('logger'):
        logger = kwargs.get('logger')

    f = open(infile)
    dataStr = f.read()
    data = dataStr.splitlines()
    if len(data[-1])==0:
        data.pop(-1)
    if iops.lower() == 'iops':
        if rwm == 'mix':
            #if not os.path.exists(outfile):
            f = open(outfile, 'w')
            f.write('Block size, IO type, Jobs, ' +
                     'Queue Depth, WR/RD, IOPS, Lantency(us), ' +
                     'Qos(us) 99%, Qos(us) 99_9%, Qos(us) 99_99%, ' +
                     'WR/RD, IOPS, Lantency(us), Qos(us) 99%, ' +
                     'Qos(us) 99_9%, Qos(us) 99_99%\n')
            f.close()

            for i in data:
                oneCaseList = i.split(';')
                if 'Precondition' in oneCaseList[2]:
                    continue
                caseNameList = oneCaseList[2].split('_')
                ioType = caseNameList[1][0].upper() + \
                         caseNameList[1][1:] + ' ' + \
                         caseNameList[2] + ' ' + \
                         caseNameList[3]
                # block size, io type, jobs, qDepth, read, IOPS, clat, qos99, qos99.9, qos99.99, write, IOPS, clat, qos99, qos99.9, qos99.99
                onCaseRes = caseNameList[0] + ',' + ioType + ',' + caseNameList[4] + ',' +\
                            caseNameList[5] + ',read,' + oneCaseList[7] + ',' +\
                            oneCaseList[15].split('.')[0] + ',' +\
                            oneCaseList[29].split('=')[1] + ',' +\
                            oneCaseList[31].split('=')[1] + ',' + \
                            oneCaseList[33].split('=')[1] + ',write,' + \
                            oneCaseList[48] + ',' + \
                            oneCaseList[56].split('.')[0] + ',' + \
                            oneCaseList[70].split('=')[1] + ',' + \
                            oneCaseList[72].split('=')[1] + ',' + \
                            oneCaseList[74].split('=')[1] + '\n'
                f = open(outfile, 'a')
                f.write(onCaseRes)
                f.close()

        elif rwm == 'p':
            #if not os.path.exists(outfile):
            f = open(outfile, 'w')
            f.write(
                'Block size, IO type, WR/RD, Jobs, ' +
                'Queue Depth, IOPS, Lantency(us), ' +
                'Qos(us) 99%, Qos(us) 99_9%, ' +
                'Qos(us) 99_99%\n'
            )
            f.close()
            for i in data:
                oneCaseList = i.split(';')
                caseName = oneCaseList[2]
                caseNameList = caseName.split('_')
                if len(caseNameList) > 2:
                    if 'seq' in caseNameList[3]:
                        caseNameList[3] = re.sub('seq', 'Sequential', caseNameList[3])
                    elif 'random' in caseNameList[1]:
                        caseNameList[3] = re.sub('random', 'Random', caseNameList[3])
                if 'RD' in caseName:
                    # block size, io type, wr/rd, jobs, qDepth, read, IOPS, clat, qos99, qos99.9, qos99.99
                    onCaseRes = caseNameList[0] + ',' + caseNameList[1] + ',' + \
                                caseNameList[2] + ',' + caseNameList[3] + ',' + \
                                caseNameList[4] + ',' + oneCaseList[7]  + ',' + \
                                oneCaseList[15].split('.')[0] + ',' + \
                                oneCaseList[29].split('=')[1] + ',' + \
                                oneCaseList[31].split('=')[1] + ',' + \
                                oneCaseList[33].split('=')[1] + '\n'
                    f = open(outfile, 'a')
                    f.write(onCaseRes)
                    f.close()
                elif 'WR' in caseName:
                    # block size, io type, wr/rd, jobs, qDepth, write, IOPS, clat, qos99, qos99.9, qos99.99
                    onCaseRes = caseNameList[0] + ',' + caseNameList[1] + ',' \
                                + caseNameList[2] + ',' + caseNameList[3] \
                                + ',' + caseNameList[4] + ',' + oneCaseList[48] + ',' \
                                + oneCaseList[56].split('.')[0] + ',' \
                                + oneCaseList[70].split('=')[1] + ',' \
                                + oneCaseList[72].split('=')[1] + ',' \
                                + oneCaseList[74].split('=')[1] + '\n'
                    f = open(outfile, 'a')
                    f.write(onCaseRes)
                    f.close()
                else:
                    logger.error('Incorrect log')
        else:
            logger.error('Incorrect type')

    elif iops.lower() == 'bw':
        if rwm == 'mix':
            # if not os.path.exists(outfile):
            f = open(outfile, 'w')
            f.write('Block size, IO type, Jobs, Queue Depth, ' +
                    'WR/RD, Bandwidth(kB/s), Lantency(us), Qos(us) 99%, ' +
                    'Qos(us) 99_9%, Qos(us) 99_99%, WR/RD, Bandwidth(kB/s), ' +
                    'Lantency(us), Qos(us) 99%, Qos(us) 99_9%, Qos(us) 99_99%\n')
            f.close()

            for i in data:
                oneCaseList = i.split(';')
                if 'Precondition' in oneCaseList[2]:
                    continue
                caseNameList = oneCaseList[2].split('_')
                ioType = caseNameList[1][0].upper() + \
                         caseNameList[1][1:] + ' ' + \
                         caseNameList[2] + ' ' + \
                         caseNameList[3]
                # block size, io type, jobs, qDepth, read, bw, clat, qos99, qos99.9, qos99.99, write, bandwidth, clat, qos99, qos99.9, qos99.99
                onCaseRes = caseNameList[0] + ',' + ioType + ',' + \
                            caseNameList[4] + ',' + caseNameList[5] + \
                            ',read,' + oneCaseList[6] + ',' + \
                            oneCaseList[15].split('.')[0] + ',' + \
                            oneCaseList[29].split('=')[1] + ',' + \
                            oneCaseList[31].split('=')[1] + ',' + \
                            oneCaseList[33].split('=')[1] + ',write,' + \
                            oneCaseList[47] + ',' + \
                            oneCaseList[56].split('.')[0] + ',' + \
                            oneCaseList[70].split('=')[1] + ',' + \
                            oneCaseList[72].split('=')[1] + ',' + \
                            oneCaseList[74].split('=')[1] + '\n'
                f = open(outfile, 'a')
                f.write(onCaseRes)
                f.close()
        elif rwm == 'p':
            #if not os.path.exists(outfile):
            f = open(outfile, 'w')
            f.write(
                'Block size, IO type, WR/RD, Jobs, Queue Depth, ' +
                'Bandwidth(kB/s), Lantency(us), Qos(us) 99%, ' +
                'Qos(us) 99_9%, Qos(us) 99_99%\n'
            )
            f.close()
            for i in data:
                oneCaseList = i.split(';')
                caseName = oneCaseList[2]
                caseNameList = caseName.split('_')
                if len(caseNameList) > 2:
                    if 'seq' in caseNameList[1]:
                        caseNameList[1] = re.sub('seq', 'Sequential', caseNameList[1])
                    elif 'random' in caseNameList[1]:
                        caseNameList[1] = re.sub('random', 'Random', caseNameList[1])
                if 'RD' in caseName:
                    # block size, io type, wr/rd, jobs, qDepth, read, bw, clat, qos99, qos99.9, qos99.99
                    onCaseRes = caseNameList[0] + ',' + caseNameList[1] + ',' + \
                                caseNameList[2] + ',' + caseNameList[3] + ',' + \
                                caseNameList[4] + ',' + oneCaseList[6] + ',' + \
                                oneCaseList[15].split('.')[0] + ',' + \
                                oneCaseList[29].split('=')[1] + ',' + \
                                oneCaseList[31].split('=')[1] + ',' + \
                                oneCaseList[33].split('=')[1] + '\n'
                    f = open(outfile, 'a')
                    f.write(onCaseRes)
                    f.close()
                elif 'WR' in caseName:
                    # block size, io type, wr/rd, jobs, qDepth, write, bandwidth, clat, qos99, qos99.9, qos99.99
                    onCaseRes = caseNameList[0] + ',' + caseNameList[1] + ',' + \
                                caseNameList[2] + ',' + caseNameList[3] + ',' + \
                                caseNameList[4] + ',' + oneCaseList[47] + ',' + \
                                oneCaseList[56].split('.')[0] + ',' + \
                                oneCaseList[70].split('=')[1] + ',' + \
                                oneCaseList[72].split('=')[1] + ',' + \
                                oneCaseList[74].split('=')[1] + '\n'
                    f = open(outfile, 'a')
                    f.write(onCaseRes)
                    f.close()
                else:
                    logger.error('Incorrect log')
        else:
            logger.error('Incorrect type')


