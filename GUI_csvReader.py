# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guiqwt/__init__.py for details)

"""Simple application based on guiqwt and guidata"""

from guidata.qt.QtGui import QMainWindow, QMessageBox, QSplitter, QListWidget, QAction, QIcon, QFont
from guidata.qt.QtCore import (QSize, QT_VERSION_STR, PYQT_VERSION_STR, Qt, 
                               SIGNAL)
from guidata.qt.compat import getopenfilename

import sys, platform
from functools import partial
import numpy as np


from guidata.dataset.qtwidgets import DataSetEditGroupBox
from guidata.dataset.dataitems import ChoiceItem
from guidata.configtools import get_icon
from guidata.qthelpers import create_action, add_actions, get_std_icon
from guidata.utils import update_dataset
from guidata.py3compat import to_text_string

from guiqwt.config import _
from guiqwt.plot import CurveDialog
from guiqwt.builder import make
from guiqwt.signals import SIG_LUT_CHANGED
from guiqwt import io

from Model import CsvFileModel
from Model import CsvParam
from histogram import HistogramWindow


APP_NAME = _("CSV Reader")
VERSION = '1.0.0'


class CsvParamNew(CsvParam):
    _hide_data = True
    _hide_size = False
    type = ChoiceItem(_("Type"),
                      (("rand", _("random")), ("zeros", _("zeros"))))

class ImageListWithProperties(QSplitter):
    # Define View的部分    
    def __init__(self, parent):
        QSplitter.__init__(self, parent)
        # List Widget
        self.csvlist = QListWidget(self)
        self.csvlist.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        plotCSV = QAction(self)        
        plotCSV.setText("Plot")
        plotCSV.triggered.connect(self.plotCSV)        
        delete = QAction(self)
        delete.setText("Remove")      
        delete.triggered.connect(self.removeItem)
        extractCSV = QAction(self)        
        extractCSV.setText("Extract to Arrays")
        extractCSV.triggered.connect(self.extractArray)    
        self.csvlist.addAction(plotCSV)
        self.csvlist.addAction(extractCSV)
        self.csvlist.addAction(delete)
        
        self.addWidget(self.csvlist)
        
        # Properties widget
        self.properties = DataSetEditGroupBox(_("參數(Properties)"), CsvParam)
        self.properties.setEnabled(False)
        self.addWidget(self.properties)
        
    def plotCSV(self):
        self.emit(SIGNAL("PLOT"))
    def removeItem(self):
        self.emit(SIGNAL("REMOVE"))
    def extractArray(self):
        self.emit(SIGNAL("EXTRACT_ARRAY"))
        
class ArrayListWithProperties(QSplitter):
    # Define View的部分    
    def __init__(self, parent):
        QSplitter.__init__(self, parent)
        # List Widget
        self.arraylist = QListWidget(self)
        self.arraylist.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        newArray = QAction(self)        
        newArray.setText("Paste Array (no header name)")
        newArray.triggered.connect(self.pasteArray)        
        newArrayWithName = QAction(self)        
        newArrayWithName.setText("Paste Array (with header name)")
        newArrayWithName.triggered.connect(self.pasteArrayWithName)        
        plotArray = QAction(self)        
        plotArray.setText("Plot Array")
        plotArray.triggered.connect(self.plotArray)       
        modifyArray = QAction(self)        
        modifyArray.setText("Modify Array(Calibration)")
        modifyArray.triggered.connect(self.modifyArray)       
        plotScatter = QAction(self)        
        plotScatter.setText("Plot Scatter")
        plotScatter.triggered.connect(self.plotScatter)       
        plotHist = QAction(self)        
        plotHist.setText("Plot Histogram")
        plotHist.triggered.connect(self.plotHist)        
        delete = QAction(self)
        delete.setText("Remove")      
        delete.triggered.connect(self.removeItem)
        curveDialog = QAction(self)
        curveDialog.setText("Open Curve Dialog")      
        curveDialog.triggered.connect(self.openCurveDialog)
        self.arraylist.addAction(newArray)        
        self.arraylist.addAction(newArrayWithName)
        self.arraylist.addAction(plotArray)
        self.arraylist.addAction(plotScatter)
        self.arraylist.addAction(plotHist)
        self.arraylist.addAction(modifyArray)
        self.arraylist.addAction(curveDialog)
        self.arraylist.addAction(delete)
        
        self.addWidget(self.arraylist)
        
        # Properties widget
        self.properties = DataSetEditGroupBox(_("參數(Properties)"), CsvParam)
        self.properties.setEnabled(False)
        self.addWidget(self.properties)   
    def pasteArray(self):
        self.emit(SIGNAL("PASTE_NO_NAME"))
    def pasteArrayWithName(self):
        self.emit(SIGNAL("PASTE_WITH_NAME"))
    def plotHist(self):        
        self.emit(SIGNAL("PLOT_HISTOGRAM"))
    def plotArray(self):
        self.emit(SIGNAL("PLOT"))
    def modifyArray(self):
        self.emit(SIGNAL("MODIFY_ARRAY"))
    def plotScatter(self):
        self.emit(SIGNAL("PLOT_SCATTER"))
    def removeItem(self):
        self.emit(SIGNAL("REMOVE"))
    def openCurveDialog(self):
        self.emit(SIGNAL("OPEN_CURVEDIALOG"))
        
        
class CentralWidget(QSplitter):
    def __init__(self, parent, toolbar):
        QSplitter.__init__(self, parent)
        # Define csvModel 提供csv處理的Model
        self.csvmodel = CsvFileModel()
        self.selectedRow = -1
        
        #connect error message
        self.connect(self.csvmodel, SIGNAL("ERROR_NOT_NONAME_ARRAY"),partial(self.showErrorMessage,"NOT_NONAME_ARRAY"))
        
        # 連接csvlist與製造ImageListWithProperties
        imagelistwithproperties = ImageListWithProperties(self)    
        
        self.addWidget(imagelistwithproperties)
        self.csvlist = imagelistwithproperties.csvlist
        self.connect(imagelistwithproperties, SIGNAL("PLOT"), partial(self.csvmodel.plotCSV, self.csvlist))
        self.connect(imagelistwithproperties, SIGNAL("REMOVE"), partial(self.csvmodel.removeCSV, self.csvlist))
        self.connect(imagelistwithproperties, SIGNAL("EXTRACT_ARRAY"), partial(self.csvmodel.extractArray, self.csvlist))
        
        # View signal connect
        self.connect(self.csvlist, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),partial(self.csvmodel.plotCSV, self.csvlist))
        self.connect(self.csvlist, SIGNAL("currentRowChanged(int)"), self.current_item_changed)
        self.connect(self.csvlist, SIGNAL("itemSelectionChanged()"), self.selection_changed)
        
        self.properties = imagelistwithproperties.properties
        self.connect(self.properties, SIGNAL("apply_button_clicked()"), self.properties_changed)

        # CsvModel signal connect
        self.connect(self.csvmodel, SIGNAL("CSV_UPDATED"),self.refresh_list)
        self.connect(self.csvmodel, SIGNAL("ARRAY_UPDATED"),self.refresh_array_list)

        # 製造ArrayListWithProperties
        self.arraylistwithproperties = ArrayListWithProperties(self)        
        self.arraylist = self.arraylistwithproperties.arraylist    
        self.addWidget(self.arraylistwithproperties)
        self.connect(self.arraylistwithproperties, SIGNAL("PASTE_NO_NAME"), partial(self.csvmodel.pasteArrayNoName, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("PASTE_WITH_NAME"), partial(self.csvmodel.pasteArrayWithName, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("PLOT"), partial(self.csvmodel.plotArray, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("MODIFY_ARRAY"), partial(self.csvmodel.modifyArray, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("PLOT_SCATTER"), partial(self.csvmodel.plotScatter, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("PLOT_HISTOGRAM"), self.plotHist)
        self.connect(self.arraylistwithproperties, SIGNAL("REMOVE"), partial(self.csvmodel.removeArray, self.arraylist))
        self.connect(self.arraylistwithproperties, SIGNAL("OPEN_CURVEDIALOG"), self.openCurveDialog)
        
        #arraylist action signal
        self.connect(self.arraylist, SIGNAL("currentRowChanged(int)"), self.array_current_item_changed)
        self.arrayproperties = self.arraylistwithproperties.properties
        self.connect(self.arrayproperties, SIGNAL("apply_button_clicked()"), self.array_properties_changed)
        self.connect(self.arraylist, SIGNAL("itemSelectionChanged()"), self.array_selection_changed)
        self.connect(self.arraylist, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),partial(self.csvmodel.plotArray, self.arraylist))
        

        # 設定基本properity
        self.setContentsMargins(10, 10, 10, 10)
        self.setOrientation(Qt.Vertical)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.setHandleWidth(10)
        self.setSizes([1, 2])
        
    def refresh_list(self):
        self.csvlist.clear()
        for csv in self.csvmodel.csvName:
            self.csvlist.addItem(csv)
        
    def refresh_array_list(self):
        self.arraylist.clear()
        for array in self.csvmodel.arrayName:
            self.arraylist.addItem(array)            
        
    def selection_changed(self):
        """Image list: selection changed, make right properity box selectable"""
        row = self.csvlist.currentRow()
        self.properties.setDisabled(row == -1)
        
    def array_selection_changed(self):
        """Array list: selection changed, make right properity box selectable"""
        row = self.arraylist.currentRow()
        self.arrayproperties.setDisabled(row == -1)
        
    def current_item_changed(self, row):
        """Image list: current image changed"""
        #csvdata, csvname = self.csvmodel.csvData[row], self.csvmodel.csvName[row]
        update_dataset(self.properties.dataset, self.csvmodel.csv[row])
        self.properties.get()        
        
    def array_current_item_changed(self, row):
        """Image list: current image changed"""
        #csvdata, csvname = self.csvmodel.csvData[row], self.csvmodel.csvName[row]
        update_dataset(self.arrayproperties.dataset, self.csvmodel.array[row])
        self.arrayproperties.get()
        
    def plotHist(self):        
        self.histWindow = HistogramWindow(self.csvmodel.arrayData[self.arraylist.currentRow()], self.csvmodel.arrayName[self.arraylist.currentRow()])
        self.histWindow.show()
        
    def openCurveDialog(self):        
        self.curvedialog = CurveDialog(edit=False, toolbar=True, wintitle="CurveDialog", options=dict(title="Title", xlabel="xlabel", ylabel="ylabel"))
        plot = self.curvedialog.get_plot()
        for array in self.csvmodel.array:
            item = make.curve(np.array(range(array.data.size)),array.data, color="b")
            plot.add_item(item)
        plot.set_axis_font("left", QFont("Courier"))
        self.curvedialog.get_itemlist_panel().show()
        plot.set_items_readonly(False)
        self.curvedialog.show()
#         
#==============================================================================
#     def lut_range_changed(self):
#         row = self.imagelist.currentRow()
#         self.lut_ranges[row] = self.item.get_lut_range()
#==============================================================================
        
#==============================================================================
#     def show_data(self, data, lut_range=None):
#         plot = self.imagewidget.plot
#         if self.item is not None:
#             self.item.set_data(data)
#             if lut_range is None:
#                 lut_range = self.item.get_lut_range()
#             self.imagewidget.set_contrast_range(*lut_range)
#             self.imagewidget.update_cross_sections()
#         else:
#             self.item = make.image(data)
#             plot.add_item(self.item, z=0)
#         plot.replot()
#==============================================================================
        
    def properties_changed(self):
        """The properties 'Apply' button was clicked: updating image"""
        row = self.csvlist.currentRow()
        csvdata = self.csvmodel.csv[row]
        update_dataset(csvdata, self.properties.dataset)
        self.csvmodel.csvName[row] =csvdata.title
        self.refresh_list()
        #self.show_data(image.data)
    
    def array_properties_changed(self):
        """The properties 'Apply' button was clicked: updating image"""
        print ("apply button click")
        row = self.arraylist.currentRow()
        arraydata = self.csvmodel.array[row]
        update_dataset(arraydata, self.arrayproperties.dataset)
        self.csvmodel.arrayName[row] =arraydata.title
        self.refresh_array_list()
#==============================================================================
#     def add_image(self, image):
#         self.images.append(image)
#         #self.lut_ranges.append(None)
#         self.refresh_list()
#         self.imagelist.setCurrentRow(len(self.images)-1)
#         plot = self.imagewidget.plot
#         plot.do_autoscale()
#==============================================================================
    
    #def add_csv_from_file(self, filename):
    def showErrorMessage(self, message):
        print ("error")
        if message=="NOT_NONAME_ARRAY":
            QMessageBox.about(self, "Error message box", "Please make sure the data in the clip board is an array")        

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setup()
        
    def setup(self):
        """Setup window parameters"""
        self.setWindowIcon(QIcon("Chicken.png"))
        self.setWindowTitle(APP_NAME)
        self.resize(QSize(800, 600))
        
        # Welcome message in statusbar:
        status = self.statusBar()
        status.showMessage(_("Welcome to guiqwt application example! 有人注意到這邊有字嗎"), 5000)
        
        # File menu
        file_menu = self.menuBar().addMenu(_("File"))
        new_action = create_action(self, _("New..."),
                                   shortcut="Ctrl+N",
                                   icon=get_icon('filenew.png'),
                                   tip=_("Create a new image, Ctrl+N"),
                                   triggered=self.new_csv)
        open_action = create_action(self, _("Open..."),
                                    shortcut="Ctrl+O",
                                    icon=get_icon('fileopen.png'),
                                    tip=_("Open a CSV file, Ctrl+O"),
                                    triggered=self.open_csv)
        quit_action = create_action(self, _("Quit"),
                                    shortcut="Ctrl+Q",
                                    icon=get_std_icon("DialogCloseButton"),
                                    tip=_("Quit application, Ctrl+Q"),
                                    triggered=self.close)
        add_actions(file_menu, ( new_action, open_action, None, quit_action))  #
        
        # Help menu
        help_menu = self.menuBar().addMenu("?")
        about_action = create_action(self, _("About..."),
                                     icon=get_std_icon('MessageBoxInformation'),
                                     triggered=self.about)
        add_actions(help_menu, (about_action,))
        
        main_toolbar = self.addToolBar("Main")
        add_actions(main_toolbar, (new_action, open_action, ))  #
        
        # Set central widget:
        toolbar = self.addToolBar("default")   # Image toolbar: Image
        self.mainwidget = CentralWidget(self, toolbar)
        self.setCentralWidget(self.mainwidget)
        
    #------?
    def about(self):
        QMessageBox.about( self, _("About ")+APP_NAME,
              """<b>%s</b> v%s<p>%s Max Huang
              <br>Copyright &copy; 2015 Garmin
              <p>Python %s, Qt %s, PyQt %s %s %s""" % \
              (APP_NAME, VERSION, _("Developped by"), platform.python_version(),
               QT_VERSION_STR, PYQT_VERSION_STR, _("on"), platform.system()) )
        
    #------I/O
    def new_csv(self):
        """Create a new image"""
        imagenew = CsvParamNew(title=_("Create a new CSV"))
        if not imagenew.edit(self):
            return
        self.mainwidget.csvmodel.newCSV(imagenew)
    
    def open_image(self):
        """Open image file"""
        saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdout = None
        filename, _filter = getopenfilename(self, _("Open"), "",
                                            io.iohandler.get_filters('load'))
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
        if filename:
            self.mainwidget.add_image_from_file(filename)
    
    def open_csv(self):
        """Open csv file"""
        saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdout = None
        filename, _filter = getopenfilename(self, _("Open a CSV file"), "",
                                            io.iohandler.get_filters('load'))
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
        if filename:
            self.mainwidget.csvmodel.addCSV(filename)
            
    def plotCenterWidget(self):
        """Plot the center widget"""
#==============================================================================
#         plot=self.mainwidget.imagewidget.plot
#         curve = make.curve(self.model.tmp.index,self.model.tmp.iloc[:,0].values,"ab", "r-")
#         plot.add_item(curve)
#         curve = make.curve(self.model.tmp.index,self.model.tmp.iloc[:,1].values,"ab", "g-")
#         plot.add_item(curve)
#         curve = make.curve(self.model.tmp.index,self.model.tmp.iloc[:,2].values,"ab", "b-")
#         plot.add_item(curve)
#         curve = make.curve(self.model.tmp.index,self.model.tmp.iloc[:,3].values,"ab", "k-")
#         plot.add_item(curve)        
#         plot.do_autoscale()
#         plot.replot()
#==============================================================================
        
if __name__ == '__main__':
    from guidata import qapplication
    app = qapplication()
    window = MainWindow()
    window.show()
    app.exec_()
