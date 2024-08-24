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
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    """Load Beeline class from file Beeline.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .beeline import Beeline
    return Beeline(iface)
