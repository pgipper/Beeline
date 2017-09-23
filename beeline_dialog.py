# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeelineDialog
                                 A QGIS plugin
 Connect points along great circles
                             -------------------
        begin                : 2017-09-10
        copyright            : (C) 2017 by Peter Gipper
        email                : peter.gipper@geosysnet.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic
from beeline_dialog_base import Ui_BeelineDialogBase


class BeelineDialog(QtGui.QDialog):
    def __init__(self):
        """Constructor."""
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.ui = Ui_BeelineDialogBase()
        self.ui.setupUi(self)
        self.ui.selectFilename.clicked.connect(self.browse)
        self.ui.shapefileOutput.toggled.connect(self.radio_shapefile)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.oldPath = ''

    def browse(self):
        """Opens a window to set the location of the output file."""
        fileName0 = QtGui.QFileDialog.getSaveFileName(self, 'Save as', self.oldPath, "Shapefile (*.shp);;All files (*)")
        fileName = os.path.splitext(str(fileName0))[0]+'.shp'
        if os.path.splitext(str(fileName0))[0] != '':
            self.oldPath = os.path.dirname(fileName)
        layername = os.path.splitext(os.path.basename(str(fileName)))[0]
        if (layername=='.shp'):
            return
        self.ui.outputFilename.setText(fileName)

    def radio_shapefile(self):
        """Choose between output as memory layer or as shapefile"""
        if self.ui.shapefileOutput.isChecked():
            self.ui.addToCanvas.setEnabled(True)
            self.ui.outputFilename.setEnabled(True)
            self.ui.selectFilename.setEnabled(True)
            self.ui.label_4.setEnabled(False)
        else:
            self.ui.addToCanvas.setEnabled(False)
            self.ui.outputFilename.setEnabled(False)
            self.ui.outputFilename.clear()
            self.ui.selectFilename.setEnabled(False)
            self.ui.label_4.setEnabled(False)
