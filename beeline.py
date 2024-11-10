# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Beeline
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

from qgis.PyQt.QtGui import QAction, QIcon
from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from processing import execAlgorithmDialog

from .beeline_algorithm import BeelineProvider


class Beeline:
    """QGIS Plugin Implementation."""

    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        self.provider = BeelineProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unloadProcessing(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        self.beelineAction = QAction()
        self.beelineAction.setIcon(QIcon(icon_path))
        self.beelineAction.triggered.connect(self.run)
        self.toolbar = self.iface.addToolBar('Beeline toolbar')
        self.toolbar.addAction(self.beelineAction)

    def unload(self):
        self.unloadProcessing()
        self.toolbar.deleteLater()
        self.beelineAction.deleteLater()

    def run(self):
        execAlgorithmDialog('beelines:beelines', {})
