import re
import yaml
import sys
import os
import traceback

class YamlProfile():
    def __init__(self):
        pass
    
    @classmethod
    def parse_single_profile(cls, yaml_file):
        '''
        description: parse projects' profiles in yaml
        author: yuhanhou
        params: yaml_file, yaml file contains the projects config info
        return: yaml data , dict or list according to the yaml format 
                all key of the dict is lowercase for easy typing in code.
        '''  
        data = None     
        try:
            with open(yaml_file,'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
        except IOError as e:
            sys.exit('IOError: ' + str(e))
        except yaml.YAMLError as ye:
            sys.exit('YAMLError: ' + str(ye))
        

        # if isinstance(data, dict):
        #     cls.lowercase_profile_keys(data)
            

        return data


    @classmethod
    def lowercase_profile_keys(cls, kwargs):
        '''
        description: change all common keys of the profile except names to lowercase
                     and change all the non-string keys to string keys
        author: yuhanhou
        params: kwargs, dict data structure parsed by yaml
        return: N/A
        '''
        if isinstance(kwargs, dict):
            for k in kwargs:
            
                if type(k) == str and not k.islower() and not re.search(r'\d', k):
                    value = kwargs.pop(k)
                    kwargs[k.lower()] = value
                    cls.lowercase_profile_keys(value)
                else:
                    if type(k) != str:
                        value = kwargs.pop(k)
                        kwargs[str(k)] = value
                        
                    cls.lowercase_profile_keys(kwargs.get(k))