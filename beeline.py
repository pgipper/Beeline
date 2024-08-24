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
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QProgressBar
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsFeature, QgsVectorFileWriter, QgsPointXY, QgsGeometry, \
    QgsDistanceArea
from qgis.gui import QgisInterface

# Initialize Qt resources from file resources.py
from Beeline import resources_rc
# Import the code for the dialog
from Beeline.beeline_dialog import BeelineDialog
import os.path


class Beeline:
    """QGIS Plugin Implementation."""

    def __init__(self, iface: QgisInterface):
        self.iface = iface

        # Create the dialog and keep reference
        self.dlg = BeelineDialog()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/Beeline/icon.svg'
        self.beelineAction = QAction(QIcon(icon_path), 'Beeline', self.iface.mainWindow())
        self.beelineAction.triggered.connect(self.run)
        self.iface.addPluginToMenu('Beeline', self.beelineAction)
        self.iface.addToolBarIcon(self.beelineAction)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu('Beeline', self.beelineAction)
        self.iface.removeToolBarIcon(self.beelineAction)

    def showMessage(self, message, level=Qgis.Info):
        """Pushes a message to the Message Bar"""
        self.iface.messageBar().pushMessage(message, level, self.iface.messageTimeout())

    def populate(self):
        """Populate the dropdown menu with point vector layers"""

        self.dlg.cmbInputLayer.clear()
        for legend in QgsProject.instance().layerTreeRoot().findLayers():
            layer = QgsProject.instance().mapLayer(legend.layerId())

            if type(layer) == QgsVectorLayer and layer.geometryType() == 0:
                self.dlg.cmbInputLayer.addItem(layer.name())

    def run(self):
        """Run method that performs all the real work"""

        # Populate the Dropdown Menu (ComboBox)
        self.populate()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:

            # Check for a valid Input Layers in the project
            point_layers = []
            layers = QgsProject.instance().mapLayers()

            for key in layers:
                # Check the layer geometry type (0 for points, 1 for lines, and 2 for polygons)
                if type(layers[key])== QgsVectorLayer and layers[key].geometryType() == 0:
                    point_layers.append(layers[key])
            if len(point_layers) == 0:
                self.showMessage('No layers to process. Please add a point layer to your project.', Qgis.Warning)
                return

            # Get input layer by name (index may change)
            layer_name = self.dlg.cmbInputLayer.currentText()
            inputLayer = QgsProject.instance().mapLayersByName(layer_name)[0]

            # Check if CRS is WGS84 (EPSG:4326)
            if inputLayer.crs().authid() != u'EPSG:4326':
                self.showMessage('Input point layer must be in geographic coordinates (WGS 84, EPSG 4326).', Qgis.Warning)
                return

            # Check if output location is set
            elif (self.dlg.shapefileOutput.isChecked() and self.dlg.outputFilename.text() == ''):
                self.showMessage('Error, no valid shapefile name for output', Qgis.Warning)
                return

            # Get output filename
            if self.dlg.shapefileOutput.isChecked():
                shapefilename = self.dlg.outputFilename.text()

            # Restrict processing to selected features
            if inputLayer.selectedFeatures():
                features = inputLayer.selectedFeatures()
            else:
                features = inputLayer.getFeatures()

            # Create a new memory layer for output
            crsString = inputLayer.crs().authid()
            outputLayer = QgsVectorLayer("LineString?crs=" + crsString, "Beelines_"+inputLayer.name(), "memory")
            pr = outputLayer.dataProvider()
            outFeat = QgsFeature()

            # Get list of points to process
            points = []
            for feature in features:
                points.append(feature.geometry().asPoint())

            # Prepare progress Bar
            progressMessageBar = self.iface.messageBar()
            progress = QProgressBar()
            progress.setMaximum(100)
            progressMessageBar.pushWidget(progress)
            def triangular(number):
                tn = 0
                for i in range(1, number+1):
                    tn += i
                return tn
            lines_total = triangular(len(points)-1)

            # Iterate over points and create arcs
            k = 1
            line_number = 0
            for point1 in points:
                for point2 in points[k:]:

                    # Set progress
                    line_number += 1
                    percent = int((line_number/float(lines_total)) * 100)
                    progress.setValue(percent)

                    # Create beeline and add as new feature
                    beelineGeometry = self.createGeodesicLine(point1, point2)
                    outFeat.setGeometry(beelineGeometry)
                    pr.addFeatures([outFeat])
                k += 1
            self.iface.messageBar().clearWidgets()

            # Handle output
            if self.dlg.memoryLayerOutput.isChecked():  # Load memory layer in canvas
                QgsProject.instance().addMapLayer(outputLayer)

            elif self.dlg.shapefileOutput.isChecked():  # Save shapefile
                QgsVectorFileWriter.writeAsVectorFormat(outputLayer, shapefilename, "utf-8", None, "ESRI Shapefile")

                if self.dlg.addToCanvas.isChecked():  # Add saved shapefile to canvas
                    layername = os.path.splitext(os.path.basename(str(shapefilename)))[0]
                    savedLayer = QgsVectorLayer(shapefilename, layername, "ogr")
                    QgsProject.instance().addMapLayer(savedLayer)

            # Show success message
            self.showMessage('Completed.', Qgis.Success)
            self.dlg.close()

    def createGeodesicLine(self, point1: QgsPointXY, point2: QgsPointXY, segmentSize: float = 100000.0) -> QgsGeometry:
        if point1.isEmpty() or point2.isEmpty():
            return QgsGeometry.fromWkt("LineString EMPTY")
        distArea = QgsDistanceArea()
        distArea.setEllipsoid('WGS84')
        interval = min(100000.0, segmentSize)  # Max segment size of 100km
        polyline = distArea.geodesicLine(point1, point2, interval=interval, breakLine=True)
        return QgsGeometry.fromMultiPolylineXY(polyline)
