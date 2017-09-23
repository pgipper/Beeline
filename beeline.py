# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Beeline
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QProgressBar
from qgis.gui import QgsMessageBar
from qgis.core import QgsGeometry, QgsFeatureRequest, QgsSpatialIndex, QgsVectorLayer, QgsFeature, QgsPoint, QgsMapLayerRegistry, QgsVectorFileWriter, QgsProject
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from beeline_dialog import BeelineDialog
# Import libs and the external geographiclib
import time, math, sys, os.path; sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/libs")
from geographiclib.geodesic import Geodesic

# define the WGS84 ellipsoid using geographiclib
geod = Geodesic.WGS84


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

    def showMessage(self, message, level=QgsMessageBar.INFO):
        """Pushes a message to the Message Bar"""
        self.iface.messageBar().pushMessage(message, level, self.iface.messageTimeout())

    def populate(self):
        """Populate the dropdown menu with point vector layers"""
        self.dlg.ui.cmbInputLayer.clear()
        for legend in QgsProject.instance().layerTreeRoot().findLayers():
            layer = QgsMapLayerRegistry.instance().mapLayer(legend.layerId())
            if layer.geometryType() == 0:
                self.dlg.ui.cmbInputLayer.addItem(layer.name())
            
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
            layers = QgsMapLayerRegistry.instance().mapLayers()
            for name, layer in layers.iteritems():
                # Check the layer geometry type (0 for points, 1 for lines, and 2 for polygons)
                if layer.geometryType() == 0:
                    point_layers.append(layer)
            if len(point_layers) == 0:
                self.showMessage(self.tr('No layers to process. Please add a point layer to your project.'), QgsMessageBar.WARNING)
                return
            
            # Get input layer by name (index may change)
            layer_name = self.dlg.ui.cmbInputLayer.currentText()
            inputLayer = QgsMapLayerRegistry.instance().mapLayersByName(layer_name)[0]

            # Check if CRS is WGS84 (EPSG:4326)
            if inputLayer.crs().authid() != u'EPSG:4326':
                self.showMessage(self.tr('Input point layer must be in geographic coordinates (WGS 84, EPSG 4326).'), QgsMessageBar.WARNING)
                return

            # Check if output location is set
            elif (self.dlg.ui.shapefileOutput.isChecked() and self.dlg.ui.outputFilename.text() == ''):
                self.showMessage(self.tr('Error, no valid shapefile name for output'),QgsMessageBar.WARNING)
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
                return number + triangular(number-1) if number else 0
            lines_total = triangular(len(points)-1)
                    
            # Iterate over points and create arcs using the geographiclib resources
            k = 1
            line_number = 0
            for point1 in points:
                for point2 in points[k:]:

                    # Set progress
                    line_number += 1
                    percent = (line_number/float(lines_total)) * 100
                    progress.setValue(percent)

                    # Calculate waypoints for smooth geodesic
                    arcpoints = []
                    arcpoints2 = []
                    l = geod.InverseLine(point1[1], point1[0], point2[1], point2[0], Geodesic.LATITUDE | Geodesic.LONGITUDE)
                    da = 1
                    n = int(math.ceil(l.a13 / da))
                    if n == 0:
                        continue
                    da = l.a13 / n
                    
                    for i in range(n + 1):
                        a = da * i
                        g = l.ArcPosition(a, Geodesic.LATITUDE | Geodesic.LONGITUDE | Geodesic.LONG_UNROLL)

                        # Make multipart feature if the line crosses longitude of 180 degree
                        if g['lon2'] >= -180:
                            arcpoints.append(QgsPoint(g['lon2'], g['lat2']))
                        else:
                            arcpoints2.append(QgsPoint(g['lon2']+360, g['lat2']))

                    if not arcpoints2:
                        polyline = QgsGeometry.fromPolyline(arcpoints)
                    else:
                        polyline = QgsGeometry.fromMultiPolyline([arcpoints, arcpoints2])

                    outFeat.setGeometry(polyline)
                    pr.addFeatures([outFeat])
                k += 1
            self.iface.messageBar().clearWidgets()
                            
            # Handle output
            if self.dlg.ui.memoryLayerOutput.isChecked():  # Load memory layer in canvas
                QgsMapLayerRegistry.instance().addMapLayer(outputLayer)

            elif self.dlg.ui.shapefileOutput.isChecked():  # Save shapefile
                QgsVectorFileWriter.writeAsVectorFormat(outputLayer, shapefilename, "utf-8", None, "ESRI Shapefile")

                if self.dlg.ui.addToCanvas.isChecked():  # Add saved shapefile to canvas
                    layername = os.path.splitext(os.path.basename(str(shapefilename)))[0]
                    savedLayer = QgsVectorLayer(shapefilename, layername, "ogr")
                    QgsMapLayerRegistry.instance().addMapLayer(savedLayer)

            # Show success message
            self.showMessage(self.tr('Completed.'), QgsMessageBar.SUCCESS)
	    self.dlg.close()
