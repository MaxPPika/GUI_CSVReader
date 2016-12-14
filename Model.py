# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 22:45:20 2015

@author: Pika
"""

#import os,sys
from PyQt4.Qt import *
from PyQt4 import QtGui
#from PyQt4.QtGui import *
#==============================================================================
# from spyderlib.qt.QtGui import *
# from spyderlib.qt.QtCore import Qt
#==============================================================================
#from spyderlib.widgets.internalshell import InternalShell

import pandas as pd
import numpy as np
import ntpath

import win32clipboard

from guiqwt import pyplot as plt
from guiqwt.pyplot import *
from guiqwt.config import _
from guiqwt.plot import CurveDialog

from guidata.py3compat import to_text_string
from guidata.dataset.datatypes import DataSet, GetAttrProp, FuncProp, ActivableDataSet
from guidata.dataset.dataitems import (IntItem, FloatArrayItem, StringItem, ChoiceItem, FloatItem, BoolItem)
                                       

indexCol=0
headerRow=20

class CsvParam(DataSet):
    _hide_data = False
    _hide_size = True
    title = StringItem(_("Title"), default=_(" csvTitle "))
    data = FloatArrayItem(_("Data")).set_prop("display",
                                              hide=GetAttrProp("_hide_data"))
    width = IntItem(_("Width(個數)"), help=_("總共幾個array"), min=1,
                    default=100).set_prop("display",
                                          hide=GetAttrProp("_hide_size"))
    height = IntItem(_("Height(長度)"), help=_("一個array的長度"), min=1,
                     default=1).set_prop("display",
                                           hide=GetAttrProp("_hide_size"))
                                           
#==============================================================================
# class ChoicesVariable(object):
#     def __init__(self):
#         self.choices = [""]
#     def set(self, choices):
#         self.choices=choices 
# choices = ChoicesVariable()            
# class Extract(DataSet):
#     type = ChoiceItem("Required Column", choices.choices)
#==============================================================================

            
class ArrayParam(DataSet):
    _hide_data = False
    _hide_size = True
    title = StringItem(_("Name"), default=_(" array name "))
    data = FloatArrayItem(_("Data")).set_prop("display", hide=GetAttrProp("_hide_data"))
    width = IntItem(_("Width(個數)"), help=_("總共幾個array"), min=1, default=100).set_prop("display", hide=GetAttrProp("_hide_size"))
    height = IntItem(_("Height(長度)"), help=_("一個array的長度"), min=1, default=1).set_prop("display", hide=GetAttrProp("_hide_size"))

class CsvFileModel (QObject):
    def __init__(self,parent=None):
        #super(Model, self).__init__(parent)  #Let parent constructor work
        QObject.__init__(self)        
        
        self.value=50
        self.tmp=None
        self.csvData=[]
        self.csvName=[]
        self.csv=[]
        self.arrayData=[]
        self.arrayName=[]
        self.array=[]
        
        
    def OnValueChange(self,signal,  value):
        #print signal
        self.value=value
        self.emit(SIGNAL("VALUE_CHANGED"))
        
#==============================================================================
#     def readCSV(self,filename):
#         self.tmp=pd.read_csv(filename,index_col=0, header=20)
#         self.emit(SIGNAL("FILE_LOADED"))
#==============================================================================
        
    def addCSV(self,filename):
        print ("Ready to extract Array")
        class CsvParam(DataSet):
            _indexprop = GetAttrProp("indextype")
            indextype = ChoiceItem("Index Column", (("A","None"),("B","Input value below")),help="If None, no need to input index column").set_prop("display", store=_indexprop)
            indexCol = IntItem("",default=0,min=0,help="first column is 0").set_prop("display", active=FuncProp(_indexprop, lambda x: x=='B'))
            _headerprop = GetAttrProp("headertype")
            headertype = ChoiceItem("Header Row", (("A","None"),("B","Input value below")),help="If None, no need to input index column").set_prop("display", store=_headerprop)
            headerRow = IntItem("", default=0,min=0,help="first column is 0").set_prop("display", active=FuncProp(_headerprop, lambda x: x=='B'))
        param = CsvParam()
        param.edit()
        if param.indextype=='A': # index None
            if param.headertype=='A': #header none        
                self.tmp=pd.read_csv(filename,index_col=None, header=None)
                print ("1")
            else:
                self.tmp=pd.read_csv(filename,index_col=None, header=param.headerRow)
                print ("2")
        else:        
            if param.headertype=='A': #header none        
                self.tmp=pd.read_csv(filename,index_col=param.indexCol, header=None)
                print ("3")
            else:
                self.tmp=pd.read_csv(filename,index_col=param.indexCol, header=param.headerRow)
                print ("4")
        print ("CSV Coulumns: "+str(self.tmp.columns))
        # deal important issue with inf, -inf, nan
        #self.tmp = self.tmp.replace(['inf','INF','Inf','-inf','-INF','-Inf',' -inf',' -INF',' -Inf','  -inf','  -INF','  -Inf',np.inf,-np.inf], np.nan)
        self.tmp=self.tmp.convert_objects(convert_numeric=True)    
        self.tmp=self.tmp.replace([np.inf, -np.inf], np.nan)
        #self.tmp = self.tmp.fillna(0)
        #print (self.tmp)
        self.csvData.append(self.tmp)
        self.csvName.append(ntpath.basename(filename))
        
        image = CsvParam()
        image.title = ntpath.basename(filename)
        image.data = self.tmp.values
        image.height, image.width = image.data.shape
        self.csv.append(image)        
        
        self.emit(SIGNAL("CSV_UPDATED"))
        
    def plotCSV(self, csvlist):
        # do plot csv figure 
        # After right click on the menu
        tmp = self.csvData[csvlist.currentRow()]
        plt.figure(self.csvName[csvlist.currentRow()])
        # add mask to avoid nan
        for x in range(tmp.columns.size):
            if x==0:
                mask=np.isfinite(tmp.iloc[:,x].values)
                print (mask)
                plt.plot(tmp.index[mask],tmp.iloc[:,x].values[mask], "b-")
            elif x==1:
                mask=np.isfinite(tmp.iloc[:,x].values)             
                print (mask)   
                plt.plot(tmp.index[mask],tmp.iloc[:,x].values[mask], "r-")
            else:
                plt.plot(tmp.index,tmp.iloc[:,x].values, "g-")
        plt.show()
        
    def removeCSV(self, csvlist):
        del self.csvName[csvlist.currentRow()]
        del self.csvData[csvlist.currentRow()]
        del self.csv[csvlist.currentRow()]
        self.emit(SIGNAL("CSV_UPDATED"))
        
        
    def pasteArrayNoName(self, arraylist):
        try:
            #arrayData = pd.read_clipboard()  
            arrayData = pd.read_clipboard(header=None)
            self.arrayData.append(arrayData)
            self.arrayName.append("new array")
            array = ArrayParam()
            array.title = "new array"
            array.data = arrayData
            array.height, array.width = array.data.shape
            self.array.append(array)        
            self.emit(SIGNAL("ARRAY_UPDATED"))     
            print ("correct array")
        except:
            print("Copy array error, make sure clipboard is a correct array")
            self.emit(SIGNAL("ERROR_NOT_NONAME_ARRAY"))
            
    def pasteArrayWithName(self, arraylist):
        try:
            #arrayData = pd.read_clipboard()  
            arrayData = pd.read_clipboard(header=0)
            self.arrayData.append(arrayData)
            self.arrayName.append(list(arrayData)[0])
            array = ArrayParam()
            array.title = list(arrayData)[0]
            array.data = arrayData
            array.height, array.width = array.data.shape
            self.array.append(array)        
            self.emit(SIGNAL("ARRAY_UPDATED"))     
            print ("correct array")
        except:
            print("Copy array error, make sure clipboard is a correct array")
            self.emit(SIGNAL("ERROR_NOT_NONAME_ARRAY"))
        
    def plotArray(self, arraylist):
        print ("Plot Array Called")
        tmp = self.arrayData[arraylist.currentRow()]
        plt.figure(self.arrayName[arraylist.currentRow()])
        for x in range(tmp.columns.size):
            # add mask to avoid nan data
            mask=np.isfinite(tmp.iloc[:,x].values)
            plt.plot(tmp.index[mask],tmp.iloc[:,x].values[mask], "b-")
        plt.show()     
        
    def modifyArray(self, arraylist):
        print ("Modify Array Called")
        tmp= self.arrayData[arraylist.currentRow()]
        name=self.arrayName[arraylist.currentRow()]
        class ModifyParam(DataSet):
            """
            Modification Parameter Setting
            Linear:  New Array = a * Original Array + b <br>
            Moving Average: Decide point number(to get average, or regard it as sinc filter)
            """
            text = StringItem("New Name", default="Modify_"+name)
            a = FloatItem("a :", default=1.0)      
            b = FloatItem("b :", default=0.0)   
            _en = GetAttrProp("enable")         
            enable = BoolItem("Enable Moving Average",
                      help="If disabled, the following parameters will be ignored",
                      default=False).set_prop("display", store=_en)                
            points = IntItem("Window",default=5, min=1).set_prop("display", active=FuncProp(_en, lambda x: x))
        #ModifyParam.active_setup()
        param = ModifyParam()
        #param.set_writeable()
        param.edit()
        newData=(tmp*param.a)+param.b
        if param.enable:
            newData = pd.rolling_mean(pd.DataFrame(newData), param.points, center=True)
            newData=newData.dropna()
            
        self.arrayData.append(newData)
        self.arrayName.append(param.text)
        array=ArrayParam()
        array.title=param.text
        array.data=newData
        array.height, array.width = array.data.shape
        self.array.append(array)
        self.emit(SIGNAL("ARRAY_UPDATED"))
    
    def plotScatter(self, arraylist):
        tmp = self.arrayData[arraylist.currentRow()]
        figure(self.arrayName[arraylist.currentRow()])
        for x in range(tmp.columns.size):
            plot(tmp.index,tmp.iloc[:,x].values, "b.")
        show()       

        
    def removeArray(self, arraylist):
        del self.arrayName[arraylist.currentRow()]
        del self.arrayData[arraylist.currentRow()]
        del self.array[arraylist.currentRow()]
        self.emit(SIGNAL("ARRAY_UPDATED"))
        
    def newCSV(self, imagenew):                      
        image = CsvParam()
        image.title = imagenew.title
        if imagenew.type == 'zeros':
            image.data = np.zeros((imagenew.width, imagenew.height))
        elif imagenew.type == 'rand':
            image.data = np.random.randn(imagenew.width, imagenew.height)  
        image.height, image.width = image.data.shape
        
        data = pd.DataFrame(image.data)
        self.csvData.append(data)
        self.csv.append(image)
        self.csvName.append(image.title)
        
        
        self.emit(SIGNAL("CSV_UPDATED"))        
        
    def extractArray(self, csvlist):
        tmp = self.csvData[csvlist.currentRow()]
        for column in tmp.columns:
            self.arrayData.append(tmp[column].to_frame())
            self.arrayName.append(str(column))
            array = ArrayParam()
            array.title = column
            array.data = tmp[column].to_frame()
            array.height, array.width = array.data.shape
            self.array.append(array)               
        self.emit(SIGNAL("ARRAY_UPDATED"))     
        

if __name__ == "__main__":
    app = QApplication([])    
    window = CsvFileModel()
    app.exec_()
    sys.exit()
