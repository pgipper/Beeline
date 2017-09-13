# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'beeline_dialog_base.ui'
#
# Created: Mon Sep 11 13:05:50 2017
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_BeelineDialogBase(object):
    def setupUi(self, BeelineDialogBase):
        BeelineDialogBase.setObjectName(_fromUtf8("BeelineDialogBase"))
        BeelineDialogBase.resize(527, 286)
        self.frame_2 = QtGui.QFrame(BeelineDialogBase)
        self.frame_2.setGeometry(QtCore.QRect(10, 110, 503, 120))
        self.frame_2.setFrameShape(QtGui.QFrame.Box)
        self.frame_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.frame_2)
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label_15 = QtGui.QLabel(self.frame_2)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_15.setFont(font)
        self.label_15.setObjectName(_fromUtf8("label_15"))
        self.verticalLayout_2.addWidget(self.label_15)
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.memoryLayerOutput = QtGui.QRadioButton(self.frame_2)
        self.memoryLayerOutput.setChecked(True)
        self.memoryLayerOutput.setObjectName(_fromUtf8("memoryLayerOutput"))
        self.horizontalLayout_9.addWidget(self.memoryLayerOutput)
        self.shapefileOutput = QtGui.QRadioButton(self.frame_2)
        self.shapefileOutput.setChecked(False)
        self.shapefileOutput.setObjectName(_fromUtf8("shapefileOutput"))
        self.horizontalLayout_9.addWidget(self.shapefileOutput)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.verticalLayout_10 = QtGui.QVBoxLayout()
        self.verticalLayout_10.setObjectName(_fromUtf8("verticalLayout_10"))
        self.label_4 = QtGui.QLabel(self.frame_2)
        self.label_4.setEnabled(False)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout_10.addWidget(self.label_4)
        self.horizontalLayout_10.addLayout(self.verticalLayout_10)
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.outputFilename = QtGui.QLineEdit(self.frame_2)
        self.outputFilename.setEnabled(False)
        self.outputFilename.setReadOnly(True)
        self.outputFilename.setObjectName(_fromUtf8("outputFilename"))
        self.horizontalLayout_3.addWidget(self.outputFilename)
        self.selectFilename = QtGui.QToolButton(self.frame_2)
        self.selectFilename.setEnabled(False)
        self.selectFilename.setObjectName(_fromUtf8("selectFilename"))
        self.horizontalLayout_3.addWidget(self.selectFilename)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_11.addLayout(self.verticalLayout_4)
        self.horizontalLayout_10.addLayout(self.horizontalLayout_11)
        self.verticalLayout_2.addLayout(self.horizontalLayout_10)
        self.addToCanvas = QtGui.QCheckBox(self.frame_2)
        self.addToCanvas.setEnabled(False)
        self.addToCanvas.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.addToCanvas.setChecked(True)
        self.addToCanvas.setObjectName(_fromUtf8("addToCanvas"))
        self.verticalLayout_2.addWidget(self.addToCanvas)
        self.verticalLayout_6.addLayout(self.verticalLayout_2)
        self.buttonBox = QtGui.QDialogButtonBox(BeelineDialogBase)
        self.buttonBox.setGeometry(QtCore.QRect(350, 240, 156, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.frame_1 = QtGui.QFrame(BeelineDialogBase)
        self.frame_1.setGeometry(QtCore.QRect(10, 10, 503, 81))
        self.frame_1.setFrameShape(QtGui.QFrame.Box)
        self.frame_1.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_1.setObjectName(_fromUtf8("frame_1"))
        self.label = QtGui.QLabel(self.frame_1)
        self.label.setGeometry(QtCore.QRect(10, 40, 161, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_17 = QtGui.QLabel(self.frame_1)
        self.label_17.setEnabled(True)
        self.label_17.setGeometry(QtCore.QRect(11, 11, 481, 13))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_17.setFont(font)
        self.label_17.setObjectName(_fromUtf8("label_17"))
        self.cmbInputLayer = QtGui.QComboBox(self.frame_1)
        self.cmbInputLayer.setGeometry(QtCore.QRect(220, 40, 271, 21))
        self.cmbInputLayer.setObjectName(_fromUtf8("cmbInputLayer"))

        self.retranslateUi(BeelineDialogBase)
        QtCore.QMetaObject.connectSlotsByName(BeelineDialogBase)

    def retranslateUi(self, BeelineDialogBase):
        BeelineDialogBase.setWindowTitle(_translate("BeelineDialogBase", "Beeline", None))
        self.label_15.setText(_translate("BeelineDialogBase", "Output :", None))
        self.memoryLayerOutput.setText(_translate("BeelineDialogBase", "Memory", None))
        self.shapefileOutput.setText(_translate("BeelineDialogBase", "Shapefile", None))
        self.label_4.setText(_translate("BeelineDialogBase", "File name", None))
        self.selectFilename.setText(_translate("BeelineDialogBase", "...", None))
        self.addToCanvas.setText(_translate("BeelineDialogBase", "add to canvas", None))
        self.label.setText(_translate("BeelineDialogBase", "Connect points from this layer:", None))
        self.label_17.setText(_translate("BeelineDialogBase", "Input:", None))

