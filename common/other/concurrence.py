'''
Created on Feb 20, 2018

@author: yuhanhou
'''
import os
import sys
import traceback
import re
from multiprocessing import Process, Queue, queues
from threading import Thread
from datetime import datetime
from common.other.log import Logger




def multi_processes(func, opts=[], log_affix=None, **kwargs):
    '''
    Description: to run function of objects in multiple processes in parallel
    Author:yuhanhou
    Params: func, function name to run of the objects or the func address provided by obj.func
            
            opts=dict|list
                    #1. dict of args for objects and func options pairs 
                    {obj1:{args=(),kwargs={}}, #args1 could be None if there is no args/options for the object's func
                    obj2:{args=(),kwargs={}}, 
                    ...}
                    #2. or  list of func's param list, suitable for single func with multiple param list to put in multiple process
                    [{args=(),kwargs={}}, {args=(),kwargs={}}, ...]
                   
            log_affix:if log rename is need add the log_affix, this is TBD
            
            kwargs, optional keyword parameters like:
                parallel_count: sigle func with signle param list to run multiple times in parallel
                logger: logger to use
            params samples of this method:
            ('func1', opts={obj1:{args=[],kwargs={}}, obj2:{args=[],kwargs={}}...}) # this will start threads by objs with their parameters,  
            (obj.func_name1, opts={'ip1':{args=[],kwargs={}}, 'ip2':{args=[],kwargs={}}...}) # this will start threads of obj.func_name1 with different parameters with defined id such ip   
            (obj.func_name1, opts=[{args=[],kwargs={}},{args=[],kwargs={}},...]) # this will start  threads of obj.func_name1 with different parameters with parameters index in list as id
            (obj.func_name2, parallel_count:5) #this will start 5 threads of obj.func_name2 which is without params, with auto generated id in range of parallel_count
    Return: results, dict with following sturcture
            {str(obj):{result:func_returns value,  #obj's str() as the key if obj as execute unit in one process
                       ip:0.0.0.0,#if ip is defined for obj
                       name:'name1' #if name is defined for obj
                       },
            ...} or
            {ip1:{'result':func_returns}
             ip2:{'result':func_returns}
            }or 
            {0:{result:func_returns value} # index of the thread as the key
             1:{result:func_returns value},
             ...
            }
    Limitation: 1. not support object as key in the return dict, using str(obj) as key instead here, use threading if needed.
                2. not support object with a session opening in it. All the objects memory content
                will be copied into the sub process with a new object id, will cause re-open 
                the session, issues could happen if switch session max is 2 or other limitations.
                The current implementation is deprecated, please improve this method before use it. 
                Multiple processes could be implemented here.
    '''
    Q = Queue()
    Q.put({})
    MAX_IN_PARALLEL = 16 #max number of processes in parallel. 16 is just an assumption value 
    logger = kwargs.get('logger')
    if logger == None:
        logger = Logger(screen_print=True)
         
    logger.info('************************multiple processes for ' + str(func) + ' starting************************')
    
    total_procs = len(opts)
    if total_procs == 0:
        total_procs = int(kwargs.get('parallel_count', 1))
    
    procs = []
    
    
    if isinstance(opts, dict):#the func need to be called by objects
        for key in opts:
            if re.search('class|instance', str(type(key)), re.I):
                p = Process(target=wrapper, args=(func, Q, str(key)), kwargs={'obj':key, 'params':opts.get(key, {})})
                procs.append(p)
                
            elif isinstance(key, str):
                p = Process(target=wrapper, args=(func, Q, key), kwargs={'params':opts.get(key, {})})
                procs.append(p)                
            
    elif isinstance(opts, list): # the func will be called directly
        if len(opts) <= 1: #simply run multiple process times of parallel_count with same params or no params of func
            count = int(kwargs.get('parallel_count', 1))
            arg = {} if len(opts) == 0 else opts[0]
            
            for i in range(count):
                p = Process(target=wrapper, args=(func, Q, i), kwargs={'params':arg})
                procs.append(p)
        else:
            for index, arg in enumerate(opts):
                p = Process(target=wrapper, args=(func, Q, index), kwargs={'params':arg})
                procs.append(p)

    in_progress_procs = []
    
    while len(procs):
        p = procs.pop()
        p.start()
        in_progress_procs.append(p) #init the queue in MAX_PROCS number
        
        if len(in_progress_procs) < MAX_IN_PARALLEL and len(procs):
            continue
        else:#wait processes to complete
            while len(in_progress_procs):
                p_in_queue = in_progress_procs.pop(0) 
                p_in_queue.join()
                
                if len(procs): #add a new proc into queue to use the available queue util all procs been started
                    p_new = procs.pop()
                    p_new.start()
                    in_progress_procs.append(p_new)

    returns = Q.get()
    
#     logger.info(results)
    
    for sub_id in returns:
        func_res = returns.get(sub_id, {}).get('result')
        matched = re.search('func_error:(.*)$', str(func_res), re.I)
        if matched:
            raise SystemExit(matched.group(1))
        
    return returns
    

def multi_threads(func, opts=[], log_affix=None, **kwargs):
    '''
    Description: to run function of objects in multiple processes in parallel
    Author:yuhanhou
    Params: func, function name to run of the objects or the func address provided by obj.func
            
            opts=dict|list
                    #1. dict of args for objects and func options pairs 
                    {obj1:{args=(),kwargs={}}, #args1 could be None if there is no args/options for the object's func
                    obj2:{args=(),kwargs={}}, 
                    ...}
                    #2. or  list of func's param list, suitable for single func with multiple param list to put in multiple process
                    [{args=(),kwargs={}}, {args=(),kwargs={}}, ...]
                   
            log_affix:if log rename is need add the log_affix, this is TBD
            
            kwargs, optional keyword parameters like:
                parallel_count: sigle func with signle param list to run multiple times in parallel
                logger: logger to use
            params samples of this method:
            ('func1', opts={obj1:{args=[],kwargs={}}, obj2:{args=(),kwargs={}}...}) # this will start threads by objs with their parameters,  
            (obj.func_name1, opts={'ip1':{args=[],kwargs={}}, 'ip2':{args=[],kwargs={}}...}) # this will start threads of obj.func_name1 with different parameters with defined id such ip   
            (obj.func_name1, opts=[{args=[],kwargs={}},{args=[],kwargs={}},...]) # this will start  threads of obj.func_name1 with different parameters with parameters index in list as id
            (obj.func_name2, parallel_count:5) #this will start 5 threads of obj.func_name2 which is without params, with auto generated id in range of parallel_count
    Return: results, dict with following sturcture
            {obj:{result:func_returns value,  #obj as the key if obj as execute unit in one thread
                       ip:0.0.0.0,#if ip is defined for obj
                       name:'name1' #if name is defined for obj
                       },
            ...} or
            {ip1:{'result':func_returns}
             ip2:{'result':func_returns}
            }or 
            {0:{result:func_returns value} # index of the thread as the key
             1:{result:func_returns value},
             ...
            }
    '''
    returns = {}
    threads = []
    MAX_IN_PARALLEL = 16 #max number of threads in parallel. 16 is just an assumption value 
    logger = kwargs.get('logger')
    if logger == None:
        logger = Logger(screen_print=True)
         
    logger.info('************************multiple threads for ' + str(func) + ' starting************************')
    
    if isinstance(opts, dict):
        for key in opts:
            if re.search('class|instance', str(type(key)), re.I):
                t = Thread(target=wrapper, args=(func, returns, key), kwargs={'obj':key, 'params':opts.get(key, {}), 'logger':logger})
                threads.append(t)
                
            elif isinstance(key, str):
                t = Thread(target=wrapper, args=(func, returns, key), kwargs={'params':opts.get(key, {}), 'logger':logger})
                threads.append(t)      
        
    elif isinstance(opts, list):
        if len(opts) <= 1: #simply run multiple threads with same params or no params of func
            count = int(kwargs.get('parallel_count', 1))
            params = {} if len(opts) == 0 else opts[0]
            
            for i in range(count):
                t = Thread(target=wrapper, args=(func, returns, i), kwargs={'params':params, 'logger':logger})
                threads.append(t)
        else:
            for index, params in enumerate(opts):
                t = Thread(target=wrapper, args=(func, returns, index), kwargs={'params':params, 'logger':logger})
                threads.append(t)

    in_progress_threads = []
    
    while len(threads):
        t = threads.pop()
        t.start()
        in_progress_threads.append(t) #init the queue in MAX_IN_PARALLEL number
        
        if len(in_progress_threads) < MAX_IN_PARALLEL and len(threads):
            continue
        else:#wait processes to complete
            while len(in_progress_threads):
                t_in_queue = in_progress_threads.pop(0) 
                t_in_queue.join()
                
                if len(threads): #add a new thread into queue to use the available queue util all procs been started
                    t_new = threads.pop()
                    t_new.start()
                    in_progress_threads.append(t_new)
    
    for th_id in returns:
        func_res = returns.get(th_id, {}).get('result')
        matched = re.search('func_error:(.*)$', str(func_res), re.I)
        if matched:
            raise SystemExit(matched.group(1))        
    
    return returns
    

def wrapper(func, Q, subID, params={}, obj=None, logger=None):
    '''
    Description:wrapper of function exection in sub process/thread
    Author:yuhanhou
    Params: func, func to be executed
            Q, Queue object or dict to store the func result in process/threading
            id: process/threading id used to distinguish the func result's owner
            obj:object owning the func #optional
            params: dict of func's args and kwargs parms
            {'args':()
             'kwargs':{}
            }
    Return: result, return value of the object's function
    '''
    res = {subID:{}}
    func_name = func 
    
    if logger == None:
        logger = Logger(screen_print=True)
    
    if obj !=None and re.search('instance|class',str(type(obj)), re.I):
        if 'name' in dir(obj) and obj.name != None:
            func_name = str(obj.name) + ' ' + func_name
            res[subID]['name'] = obj.name
        
        if 'ip' in dir(obj) and obj.ip != None:
            if 'name' not in dir(obj) or obj.name == None:
                func_name = obj.ip + ' ' + func_name      
            res[subID]['ip'] = obj.ip
            
        func = getattr(obj, func)
    
    #parse func's params list
    func_args = params.get('args', ())
    func_kwargs = params.get('kwargs', {})
    
    func_res = None
    try:        
        logger.info(str(func_name) + ' is executing...')
            
        func_res = func(*func_args, **func_kwargs)
        
    except BaseException as e: 
        logger.error('\ error in ' + str(func_name) + ' of ' + str(id))
        logger.error(sys.exc_info())
        for stack in traceback.extract_tb(sys.exc_info()[2]):
            logger.error(stack)
            
        func_res = 'func_error:' + str(e)
    
    logger.info(str(func_name) + ' ' + str(subID) + ' is done...')
    
    
    res[subID]['result'] = func_res
    
    if isinstance(Q, queues.Queue):
        result = Q.get(True)
        result.update(res)
        Q.put(result)
    else:
        Q.update(res)
       
 
def rename_log(obj, log_affix):
    '''
    Description:rename the object's log generated in process/thread
    Author:yuhanhou
    Params: obj, 
            log_affix, suffix added the new log file name
    Return: new_file, new log file name
    '''      
    if 'logger' in dir(obj):
        log_file = obj.logger.log_file
        
        if 'ip' in dir(obj) and obj.ip != None:
            log_affix = obj.ip + '_' + log_affix 
        
        if 'name' in dir(obj) and obj.name != None:
            log_affix = obj.name + '_' + log_affix 
        
        if os.path.exists('logs'):
            pass
        else:
            os.mkdir('logs')
        
        timestamp = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        new_file = 'logs/'+ log_affix + '_' + timestamp
        print('log_file is' + log_file)
        os.rename(log_file, new_file)
        
        return new_file
        
