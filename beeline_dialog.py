# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeelineDialog
                                 A QGIS plugin
 Connect points along great circles
                             -------------------
        begin                : 2017-09-10
        copyright            : (C) 2017 by Peter Gipper
        email                : petergipper@gmail.com
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

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QFileDialog

uiPath = os.path.join(os.path.dirname(__file__), 'beeline_dialog.ui')
GUI_CLASS, _ = uic.loadUiType(uiPath)


class BeelineDialog(QDialog, GUI_CLASS):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.selectFilename.clicked.connect(self.browse)
        self.shapefileOutput.toggled.connect(self.radio_shapefile)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)
        self.oldPath = ''

    def browse(self):
        """Opens a window to set the location of the output file."""
        fileName0 = QFileDialog.getSaveFileName(self, 'Save as', self.oldPath, "Shapefile (*.shp);;All files (*)")
        fileName = os.path.splitext(str(fileName0))[0]+'.shp'
        if os.path.splitext(str(fileName0))[0] != '':
            self.oldPath = os.path.dirname(fileName)
        layername = os.path.splitext(os.path.basename(str(fileName)))[0]
        if (layername=='.shp'):
            return
        self.outputFilename.setText(fileName)

    def radio_shapefile(self):
        """Choose between output as memory layer or as shapefile"""
        if self.shapefileOutput.isChecked():
            self.addToCanvas.setEnabled(True)
            self.outputFilename.setEnabled(True)
            self.selectFilename.setEnabled(True)
            self.label_4.setEnabled(False)
        else:
            self.addToCanvas.setEnabled(False)
            self.outputFilename.setEnabled(False)
            self.outputFilename.clear()
            self.selectFilename.setEnabled(False)
            self.label_4.setEnabled(False)
