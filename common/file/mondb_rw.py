import pymongo
import re
import copy

class MongoDB():

    def __init__(self,dbsname='runoobdb',setname='sites',addr='localhost',port='27017'):
        """
        description : connect mondb server
        """
        myclient = pymongo.MongoClient("mongodb://%s:%s/" % (addr,port))
        mydb = myclient[dbsname]
        self.mycol = mydb[setname]

    def add_one_data(self,dataname=None,**data):
        """
        description : add one data and data is a dict
        """
        if dataname:
          data['_id'] = dataname
        res = self.mycol.insert_one(data)
        return res.inserted_id

    def add_many_data(self,data):
        """
        description : add one data and data is a list :[{},{},{}....]
        """
        res = self.mycol.insert_many(data)
        return res.inserted_ids
    
    def del_one_data(self,**requirement):
        """
        description : del one data and need a requirement ex id = xx, or some keys
        """
        for k in copy.deepcopy(requirement).keys():
            if re.search(r'id',k,re.I):
              requirement['_id'] = requirement.pop(k)
        self.mycol.delete_one(requirement)
    
    def del_many_data(self,**requirement):
        """
        description : del many data need requirement can regex
        """
        reason = {}
        for k,v in requirement.items():
            reason[k] = {"$regex": str(v)}
            print(reason)
        self.mycol.delete_many(reason)

    def del_all_documents(self):
        """
        description : del document
        """
        self.mycol.delete_many({})

    def del_set(self):
        """
        description : del set
        """
        self.mycol.drop()

    def find_id_data(self,**requirement):
        """
        description : find data if _id = requirement
        """
        returnlist = []
        for k in copy.deepcopy(requirement).keys():
            if re.search(r'id',k,re.I):
              requirement['_id'] = requirement.pop(k)
        for tmp in self.mycol.find(requirement):
            returnlist.append(tmp)
        return returnlist
      
    def find_all(self,onlyid=False):
        """
        description : find all data return list,if onlyid=True returnlist only _id
        """
        list = []
        returnlist = []
        for data in self.mycol.find():
            list.append(data)
        if onlyid:
            for i in list:
                returnlist.append(i.get('_id'))
        else:
            returnlist = list
        return returnlist