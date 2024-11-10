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
from typing import Tuple

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon
from qgis._core import QgsFeatureRequest
from qgis.core import (Qgis, QgsFeature, QgsPointXY, QgsGeometry, QgsDistanceArea, QgsProcessingParameterFeatureSource,
                       QgsProcessingException, QgsFeatureSink, QgsFields, QgsField, QgsProcessing,
                       QgsProcessingAlgorithm, QgsProcessingProvider, QgsProcessingParameterFeatureSink, QgsProject)


class BeelineProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(BeelineAlgorithm())

    def id(self):
        return "beelines"

    def name(self):
        return "Beelines"

    def icon(self):
        return QIcon(self.svgIconPath())

    def svgIconPath(self):
        return os.path.join(os.path.dirname(__file__), "icon.svg")

    def longName(self):
        return self.name()


class BeelineAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Input Points",
                types=[QgsProcessing.SourceType.VectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Beelines"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        sinkFields = QgsFields()
        sinkFields.append(QgsField('source_id', QVariant.Int))
        sinkFields.append(QgsField('target_id', QVariant.Int))
        sinkFields.append(QgsField('distance', QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            sinkFields,
            Qgis.WkbType.LineString,
            source.sourceCrs()
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        distanceArea = QgsDistanceArea()
        distanceArea.setSourceCrs(source.sourceCrs(), QgsProject.instance().transformContext())
        distanceArea.setEllipsoid(source.sourceCrs().ellipsoidAcronym())

        # Get list of points to process
        points = []
        for feature in source.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([], source.fields())):
            if feedback.isCanceled():
                break
            points.append((feature.id(), feature.geometry().asPoint()))

        sinkFeatureCount = sum(range(len(points)))

        # Iterate over points and create arcs
        k = 1
        currenFeature = 0
        for point1_id, point1 in points:
            for point2_id, point2 in points[k:]:
                if feedback.isCanceled():
                    break

                # Set progress
                currenFeature += 1
                percent = int((currenFeature/float(sinkFeatureCount)) * 100)
                feedback.setProgress(percent)

                outFeat = QgsFeature(sinkFields)
                outFeat['source_id'] = point1_id
                outFeat['target_id'] = point2_id

                # Create beeline and add as new feature
                beelineGeometry, distance = self.createGeodesicLine(distanceArea, point1, point2)
                outFeat.setGeometry(beelineGeometry)
                outFeat['distance'] = distance
                sink.addFeature(outFeat, QgsFeatureSink.Flag.FastInsert)
            k += 1

        infoText = f"""
            Ellipsoid: {distanceArea.ellipsoid()}
            Length units: {Qgis.DistanceUnit(distanceArea.lengthUnits()).name}
        """
        feedback.pushInfo(infoText)
        return {self.OUTPUT: dest_id}

    def createGeodesicLine(self, distArea, point1: QgsPointXY, point2: QgsPointXY, segmentSize: float = 100000.0
                           ) -> Tuple[QgsGeometry, float]:
        if point1.isEmpty() or point2.isEmpty():
            return QgsGeometry.fromWkt("LineString EMPTY"), 0.0
        interval = min(100000.0, segmentSize)  # Max segment size of 100km
        polyline = distArea.geodesicLine(point1, point2, interval=interval, breakLine=True)
        distance = sum(distArea.measureLine(line) for line in polyline)
        return QgsGeometry.fromMultiPolylineXY(polyline), distance

    def name(self):
        return "beelines"

    def displayName(self):
        return "Beelines"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def shortHelpString(self):
        return """Create lines along great circles between selected points"""

    def createInstance(self):
        return BeelineAlgorithm()