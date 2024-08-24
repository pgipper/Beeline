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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.gui import QgsMessageBar
from qgis.core import *
# Initialize Qt resources from file resources.py
from Beeline import resources_rc
# Import the code for the dialog
from Beeline.beeline_dialog import BeelineDialog
# Import libs and the external geographiclib
import timeit, math, os.path


class Beeline:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Beeline_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Beeline')
        # Add a toolbar
        self.toolbar = self.iface.addToolBar(u'Beeline')
        self.toolbar.setObjectName(u'Beeline')

        # Create the dialog (after translation) and keep reference
        self.dlg = BeelineDialog()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Beeline', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/Beeline/icon.svg'
        self.add_action(
            icon_path,
            text=self.tr(u'Connect points along great circles'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Beeline'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def showMessage(self, message, level=Qgis.Info):
        """Pushes a message to the Message Bar"""
        self.iface.messageBar().pushMessage(message, level, self.iface.messageTimeout())

    def populate(self):
        """Populate the dropdown menu with point vector layers"""

        self.dlg.ui.cmbInputLayer.clear()
        for legend in QgsProject.instance().layerTreeRoot().findLayers():
            layer = QgsProject.instance().mapLayer(legend.layerId())

            if type(layer) == QgsVectorLayer and layer.geometryType() == 0:
                self.dlg.ui.cmbInputLayer.addItem(layer.name())

    def run(self):
        """Run method that performs all the real work"""

        # Populate the Dropdown Menu (ComboBox)
        self.populate()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:

            tic=timeit.default_timer()

            # Check for a valid Input Layers in the project
            point_layers = []
            layers = QgsProject.instance().mapLayers()

            for key in layers:
                # Check the layer geometry type (0 for points, 1 for lines, and 2 for polygons)
                if type(layers[key])== QgsVectorLayer and layers[key].geometryType() == 0:
                    point_layers.append(layers[key])
            if len(point_layers) == 0:
                self.showMessage(self.tr('No layers to process. Please add a point layer to your project.'), Qgis.Warning)
                return

            # Get input layer by name (index may change)
            layer_name = self.dlg.ui.cmbInputLayer.currentText()
            inputLayer = QgsProject.instance().mapLayersByName(layer_name)[0]

            # Check if CRS is WGS84 (EPSG:4326)
            if inputLayer.crs().authid() != u'EPSG:4326':
                self.showMessage(self.tr('Input point layer must be in geographic coordinates (WGS 84, EPSG 4326).'), Qgis.Warning)
                return

            # Check if output location is set
            elif (self.dlg.ui.shapefileOutput.isChecked() and self.dlg.ui.outputFilename.text() == ''):
                self.showMessage(self.tr('Error, no valid shapefile name for output'), Qgis.Warning)
                return

            # Get output filename
            if self.dlg.ui.shapefileOutput.isChecked():
                shapefilename = self.dlg.ui.outputFilename.text()

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
            toc=timeit.default_timer()
            print("processing time: ", toc-tic)

            # Handle output
            if self.dlg.ui.memoryLayerOutput.isChecked():  # Load memory layer in canvas
                QgsProject.instance().addMapLayer(outputLayer)

            elif self.dlg.ui.shapefileOutput.isChecked():  # Save shapefile
                QgsVectorFileWriter.writeAsVectorFormat(outputLayer, shapefilename, "utf-8", None, "ESRI Shapefile")

                if self.dlg.ui.addToCanvas.isChecked():  # Add saved shapefile to canvas
                    layername = os.path.splitext(os.path.basename(str(shapefilename)))[0]
                    savedLayer = QgsVectorLayer(shapefilename, layername, "ogr")
                    QgsProject.instance().addMapLayer(savedLayer)

            # Show success message
            self.showMessage(self.tr('Completed.'), Qgis.Success)
            self.dlg.close()

    def createGeodesicLine(self, point1: QgsPointXY, point2: QgsPointXY, segmentSize: float = 100000.0) -> QgsGeometry:
        if point1.isEmpty() or point2.isEmpty():
            return QgsGeometry.fromWkt("LineString EMPTY")
        distArea = QgsDistanceArea()
        distArea.setEllipsoid('WGS84')
        interval = min(100000.0, segmentSize)  # Max segment size of 100km
        polyline = distArea.geodesicLine(point1, point2, interval=interval, breakLine=True)
        return QgsGeometry.fromMultiPolylineXY(polyline)
