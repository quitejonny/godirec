# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/dialog.ui'
#
# Created: Wed May 21 22:55:59 2014
#      by: PyQt4 UI code generator 4.10.4
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(315, 132)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("folder-yellow.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayoutWidget = QtGui.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 0, 291, 101))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.LineEditPath = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.LineEditPath.setObjectName(_fromUtf8("LineEditPath"))
        self.horizontalLayout.addWidget(self.LineEditPath)
        self.ButtonDir = QtGui.QPushButton(self.verticalLayoutWidget)
        self.ButtonDir.setText(_fromUtf8(""))
        self.ButtonDir.setIcon(icon)
        self.ButtonDir.setObjectName(_fromUtf8("ButtonDir"))
        self.horizontalLayout.addWidget(self.ButtonDir)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.LineEditProjekt = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.LineEditProjekt.setObjectName(_fromUtf8("LineEditProjekt"))
        self.horizontalLayout_2.addWidget(self.LineEditProjekt)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.ButtonCreate = QtGui.QPushButton(Dialog)
        self.ButtonCreate.setGeometry(QtCore.QRect(80, 100, 141, 21))
        self.ButtonCreate.setMinimumSize(QtCore.QSize(141, 0))
        self.ButtonCreate.setObjectName(_fromUtf8("ButtonCreate"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "erzeuge Projekt", None))
        self.label.setText(_translate("Dialog", "Projekt Name:", None))
        self.ButtonCreate.setText(_translate("Dialog", "Erzeugen", None))

