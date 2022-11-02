#/usr/bin/python3
# -*- coding=utf-8 -*-

import re, csv
from pprint import pformat
from common.other.log import Logger
from collections import OrderedDict



class CSV_Parser():
    '''
    description: this class contain the operation of csv file, which is sperated by , or spaces
    '''
    def __init__(self, **kwargs):
        '''
        description:read csv files into customized data structure
        author: yuhanhou
        params: kwargs, optional keywords params:
                    logger, object of logger, default log file is csv.log
                    separator,  separator of the csv file or similar format with other separator, like #
                                default is: , spaces or tabs
        '''
        if kwargs.get('logger'):
            self.logger = kwargs.get('logger')
        else:
            self.logger = Logger(log_file='csv.log')
        self.separator = kwargs.get('separator', r'[\s\t,]+')


    def read(self, file, **kwargs):
        '''
        description:read csv files into customized data structure
        author: yuhanhou, Kail
        params: file, csv file
                kwargs: optional keyword value pairs
                    count: int number > 1, optional, lines count needed to be read counted from the first line
                           all lines will be read by default
                    head_num: int number > 0, optional, output the top head_num to a list, default is 0
                    wanted_columns: list of the wanted columns , index(int, start from 1) or column name is ok, [1, 'name', ...]
                                    DO NOT conflict it with unwanted_columns at the same time!
                    unwanted_columns: list of the unwanted columns , index or column is ok, other is the same as wanted_columns
                                    Note: the unwanted columns has the higher priority than wanted_columns
                    data_s: list(default)|dict|dinl, return type of data structure, sample:
                         1. dinl: dict in list, a list whose element is pure dict
                            dinl-> [{t1:value1, t2:value2, ...},{...}, ...]
                         2. list: pure list, a list whose element is pure list
                            list -> [[v1, v2, v3, ...] ,[v1, v2, v3, ...], ...]
                         3. dict: pure order dict, element contain:
                                title dict: {'title':'[A1, A2, ..., Amax_column]'}
                                single row dict:{'A6': {'B1':'B6', 'C1':'C6', ...}}
                            dict{
                                    {'title':'[A1, A2, ..., A.max_column]'},
                                    {'A2': {'B1':'B2', 'C1':'C2', 'D1':'D2' ...}},
                                    {'A3': {'B1':'B3', 'C1':'C3', 'D1':'D3' ...}},
                                    ...
                                    {'Amax_row': {'B1':'Bmax_row', 'C1':'Cmax_row', 'D1':'Dmax_row' ...}},
                        `       }
        return: list, dinl or dict according to the 'data_s' kw para
        '''
        data_s = kwargs.get('data_s', 'list')
        count = kwargs.get('count', 0)
        head_num = kwargs.get('head', 0)
        wanted_columns = kwargs.get('wanted_columns')
        unwanted_columns = kwargs.get('unwanted_columns')
        result = []
        lines = []

        #read lines from file:
        if not file.endswith('.csv'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    if int(count) > 0: #if count==0 will read all the lines
                        for i in range(count):
                            line = f.readline()
                            if line == '': #file end
                                break
                            else:
                                lines.append(line)
                    else:
                        lines = f.readlines()
            except OSError as e:
                self.logger.error(str(e))
                raise
            if len(lines) == 0:
                self.logger.error(file + ' is empty!')
                return result
            #parse lines into request data structure:

            #filter the raw data:
            titles = []
            values = []
            #get the real contents
            for line in lines:
                if re.search(r'^\s*$', line):
                    continue
                tmp_list = [v.strip() for v in re.split(self.separator, line)]
                if len(titles) == 0:
                    titles = tmp_list
                    continue
                values.append(tmp_list)
        else:
            with open(file) as csvfile:
                csv_list = list(csv.reader(csvfile))
            titles = csv_list[0]
            if int(count) > 0:
                values = [ i for i in csv_list[1:int(count)]]
            else:
                values = [ i for i in csv_list[1:]]

        #filter the defined columns:
        if wanted_columns and unwanted_columns:
            self.logger.warn('NOTE:unwanted_columns param has the higher priority wanted_columns at the same time!')
            #raise Exception('wanted_columns and unwanted_columns params can\'t be used at the same time!')

        del_index = []
        for i, t in enumerate(titles):
            if unwanted_columns != None and (i+1 in unwanted_columns or t in unwanted_columns):
                del_index.append(i)
            if wanted_columns != None and (i+1 not in wanted_columns and t not in wanted_columns) and i not in del_index:
                del_index.append(i)
        titles = [titles[j] for j, t in enumerate(titles) if j not in del_index]

        for contents in values:
            for i in reversed(del_index):
                del contents[i]

        if data_s == 'list':
            result.append(titles)
            result.extend(values)
        elif data_s == 'dinl':
            for contents in values:
                tmp_dict = {t:contents[i] for i, t in enumerate(titles) }
                result.append(tmp_dict)
        elif data_s == 'dict':
            result.append(titles)
            result.extend(values)
            result = self.date_trans(data=result, trans_type='list_dict')

        self.logger.debug('the data_s parsed from ' + file + ':')
        self.logger.debug(pformat(result, indent=4))
        return result


    def search_line(self, sfile, rgx):
        '''
        description: search particular line in flie
        author: Kail
        params: sfile, rgx
                sfile: the file want to be deal
                rgx:   the regular expression of wanted lines
        return: list of searched line's index
        '''
        line_idx = []
        regex = re.compile(rgx)
        with open(sfile) as f:
            rf = f.readlines()
        for i in range(len(rf)):
            if regex.search(rf[i]):
                line_idx.append(i + 1)
        return line_idx


    def del_lines(self, dfile, line_list=[], **kwargs):
        '''
        description: delete lines in file according to num in line_list
        author: Kail
        params: dfile, line_list
                sfile: the file that want to deal
                line_list:   the line list want to delete
                kwargs: optional keyword value pairs
                    nf: the new file that want to saved as
        return: None
        '''
        new_file = kwargs.get('nf')
        new_dlist = []
        with open(dfile) as f:
            rf = f.readlines()
        for i in range(len(rf)):
            if i + 1 in line_list:
                continue
            else:
                new_dlist.append(rf[i])
        if new_file:
            wirte_file = new_file
        else:
            wirte_file = dfile
        with open(wirte_file, mode='w', encoding="utf-8") as f:
            f.writelines(new_dlist)


    def date_trans(self, data, trans_type='list_dict'):
        # trans_type: list_dict, dict_list, list_dinl
        # dinl: dict in list
        '''
        description: transfer data structure from [list, dict, dinl] to another data structure [list, dict, dinl]
        author: Kail
        params: data, trans_type
                    data: data structure in three fixed format:
                         1. dinl: dict in list, a list whose element is pure dict
                            dinl-> [{t1:value1, t2:value2, ...},{...}, ...]
                         2. list: pure list, a list whose element is pure list
                            list -> [[v1, v2, v3, ...] ,[v1, v2, v3, ...], ...]
                         3. dict: pure order dict, element contain:
                                title dict: {'title':'[A1, A2, ..., Amax_column]'}
                                single row dict:{'A6': {'B1':'B6', 'C1':'C6', ...}}
                            dict{
                                    {'title':'[A1, A2, ..., A.max_column]'},
                                    {'A2': {'B1':'B2', 'C1':'C2', 'D1':'D2' ...}},
                                    {'A3': {'B1':'B3', 'C1':'C3', 'D1':'D3' ...}},
                                    ...
                                    {'Amax_row': {'B1':'Bmax_row', 'C1':'Cmax_row', 'D1':'Dmax_row' ...}},
                        `       }
                    trans_type: the transfer type choosen from:
                                    [dict_dinl, dict_list, list_dict, list_dinl, dinl_list, dinl_dict]
                                head of trans_type in raw dict
                                tail of trans_type in return dict
        return: list, dinl or dict according to the 'trans_type' para
        '''
        raw_list = []
        raw_tp = trans_type.split('_')[0]
        new_tp = trans_type.split('_')[-1]

        # transfer raw data to list
        if raw_tp == 'dict':
            title_row = data['title']
            raw_list.append(title_row)
            for k, dic in data.items():
                if k == 'title':
                    continue
                else:
                    tmp_list = [k]
                    for i, rv in enumerate(title_row):
                        tmp_list.insert(i+1, dic.get(rv))
                    raw_list.append(tmp_list)
        elif raw_tp == 'dinl':
            title_row = []
            for dic in data:
                for k in dic.keys():
                    if k in title_row:
                        continue
                    else:
                        title_row.append(k)
            raw_list.append(title_row)
            for dic in data:
                tmp_list = []
                tmp_dict = {}
                for i, v in enumerate(title_row):
                    tmp_list.insert(i, dic.get(v))
                raw_list.append(tmp_list)
        elif raw_tp == 'list':
            raw_list = data

        if new_tp == 'dict':
            dict_title = raw_list[0]
            xlsx_dict = OrderedDict()
            xlsx_dict['title'] = dict_title
            for l in raw_list[1:]:
                sub_key = l[0]
                xlsx_dict[sub_key] = OrderedDict()
                for i in range(1, len(l)):
                    xlsx_dict[sub_key][dict_title[i]] = l[i]
            return xlsx_dict
        elif new_tp == 'dinl':
            dic_in_lis = []
            titles = raw_list[0]
            for lis in raw_list[1:]:
                tmp_dict = OrderedDict()
                #tmp_dict = {v:lis[i] for i, v in enumerate(titles)}
                for i, v in enumerate(titles):
                    tmp_dict[v] = lis[i]
                dic_in_lis.append(tmp_dict)
            return dic_in_lis
        elif new_tp == 'list':
            return raw_list


    def list_action(self, list_data, action, **kwargs):
        '''
        description: deal pure list data
        author: Kail
        params: list_data: the raw pure list data
                action: which action want to deal with 'list_data', choices:
                    ['clean', 'ins_row', 'ins_col', 'del_row', 'del_col']
                     clean, select rows whose PART_NUMBER in bu29_bom_dict.keys
                     ins_row, insert a row
                     ins_col, insert a column
                     del_row, delete a row
                     del_col, delete a column
                kwargs: optional keyword value pairs
                    start_idx: the satrt [row/column] index number
                    head:      the head value of insert [row/column]
                    ins_list:  the insert [row/column] list
        return: the new list data according to 'action'
        '''
        start_idx = kwargs.get('start_idx')
        head = kwargs.get('head') # the first of empty row or column
        ins_list = kwargs.get('ins_list')
        #sort_title = kwargs.get('sort_title')
        empty_cell = None

        title_list = list_data[0]
        empty_row = [empty_cell for i in range(len(title_list))]
        empty_col = [empty_cell for i in range(len(list_data))]
        # head and ins_list only one exist
        if head:
            empty_row[0] = head
            empty_col[0] = head
        elif ins_list:
            for i, v in enumerate(ins_list):
                empty_row[i] = v
                empty_col[i] = v

        # select rows whose PART_NUMBER in bu29_bom_dict.keys
        if action == 'clean':
            abnormal_list = [title_list]
            normal_list = [title_list]
            for l in list_data[1:]:
                if l[title_list.index('PART_NUMBER')] not in bu29_bom_dict.keys():
                    abnormal_list.append(l)
                else:
                    normal_list.append(l)
            return normal_list, abnormal_list
        elif action == 'sort_column':
            return 'TBD'
        elif action == 'ins_row':
            if start_idx is None or start_idx >= len(list_data):
                list_data.append(empty_row)
            elif start_idx < len(list_data):
                list_data.insert(start_idx, empty_row)
        elif action == 'ins_col':
            if start_idx is None or start_idx >= len(title_list):
                for l in list_data:
                    l.append(empty_col[list_data.index(l)])
            elif start_idx < len(title_list):
                for l in list_data:
                    l.insert(start_idx, empty_col[list_data.index(l)])
        elif action == 'del_row':
            if start_idx < len(list_data):
                del list_data[start_idx]
        elif action == 'del_col':
            if start_idx < len(title_list):
                for l in list_data:
                    del l[start_idx]
        return list_data
