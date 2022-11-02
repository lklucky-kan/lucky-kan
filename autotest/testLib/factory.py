import re
import os
import sys
import pkgutil
from inspect import isclass
from importlib import import_module



class TestFactory():

    @classmethod
    def create_testcase(cls, lib_cls, **kwargs):
        '''
        description: this method is create the tea framework testcase lib class obj 
        author: yuhanhou
        params: lib_cls, the testcase lib class 
        return: testcase lib class obj
        '''

        #return testcase obj and testcase method
       
        
        lib_obj = lib_cls(**kwargs)
        return lib_obj


    @classmethod
    def lookup_case_lib(cls, case, team='sit', framework='tea', **kwargs):
        '''
        description: find the case related class name func name or robot file and selenium file
        author: yuhanhou
        params: case, testcase name w/o the prefix
                team, 'sit' or 'bmc' to define which package to find the testcase lib\
                framework, define which framework is used to run the testcase
                kwargs, optional kw pairs
                    testsuite: the testsuite name which equals to the module file contains the case.

        return: class mod path and testcase func name
        '''


        if framework == 'tea':
            class_obj = None
            func = None
            pkg_name = re.sub(r'\.\w+$', '', __name__, 1)



            if re.search(r'\S', team): #for future shared case which is not located in some team pkg, can use team='' shared case will defined in outside out team pkg and use a specail mod file to implement
                pkg_name += '.' + team
            
            if kwargs.get('testsuite'):
                testsuite = kwargs.get('testsuite')
                class_obj, func = cls.lookup_case_in_mods(case, pkg_name + '.' +testsuite)
            else:
                im_pkg = import_module(pkg_name)
                sub_pkgs = []
                ex_mods = []
                for importer, p, is_pkg in pkgutil.iter_modules(im_pkg.__path__):
                    if is_pkg:
                        sub_pkgs.append(pkg_name + '.' + p)
                    else:
                        ex_mods.append(pkg_name + '.' + p)

                for sub_path in sub_pkgs:
                    
                    im_sub = import_module(sub_path)
                    mods = [sub_path + '.' + m for importer, m, is_pkg in pkgutil.iter_modules(im_sub.__path__) if not is_pkg]
                    class_obj, func = cls.lookup_case_in_mods(case, mods)
                    if func:
                        break
                
            if func:
                print('preparing testcase:' + pkg_name + '.' + class_obj.__name__ + '.' + func)
            else:
                class_obj, func = cls.lookup_case_in_mods(case, ex_mods) #for furture shared case, need to consider to find ex_mods before sub pkg mods
            
            if not func:            
                sys.exit("can't find the definition of the testcase " + case + ' in ' + team + ' logic layer')
            
            return class_obj, func

        elif framework == 'robot':
            cls.lookup_robot_case(case, team)
        elif re.search('sel', framework, re.I):
            cls.lookup_sel_case(case, team)

        #return mod_path or robot file, or other framework related file

    def lookup_robot_case(cls, testcase, team='sit'):
        pass

    def lookup_sel_case(cls, testcase, team='sit'):
        pass


    @classmethod
    def lookup_case_in_mods(cls, case, modules=[]): 
        '''
        Description: lookup class object and function name by case and iterate modules
        Author:yuhanhou
        Params: case, testcase name
                modules, list of module full names, 
        Return: class_obj, the class containing the case
                func, the relevant function name for case running    
        '''
        case = re.sub(r'^test_', '', case)
        case = 'test_' + case        
                       
        found = False
        class_obj = None
        func = None
        
        for mod in modules:
            if found:
                break
            
            imp = import_module(mod)
            
            for name in dir(imp):
                if found:
                    break
                
                name_obj = getattr(imp, name)
                
                if isclass(name_obj) and name_obj.__dict__.get('__module__') == imp.__name__:
                    for f in dir(name_obj):
                        if re.search(r'^' + case + r'$', f, re.I):
                            func = f
                            class_obj = name_obj
                            found = True
                            break
                        
        return class_obj, func

     
 