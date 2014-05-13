# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/godi_rec.ui'
#
# Created: Tue May 13 23:32:46 2014
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

class Ui_GodiRec(object):
    def setupUi(self, GodiRec):
        GodiRec.setObjectName(_fromUtf8("GodiRec"))
        GodiRec.resize(338, 459)
        self.centralwidget = QtGui.QWidget(GodiRec)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 20, 311, 150))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton_play = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton_play.setObjectName(_fromUtf8("pushButton_play"))
        self.horizontalLayout.addWidget(self.pushButton_play)
        self.pushButton_stop = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton_stop.setObjectName(_fromUtf8("pushButton_stop"))
        self.horizontalLayout.addWidget(self.pushButton_stop)
        self.pushButton_rec = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton_rec.setObjectName(_fromUtf8("pushButton_rec"))
        self.horizontalLayout.addWidget(self.pushButton_rec)
        self.pushButton_cut = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton_cut.setObjectName(_fromUtf8("pushButton_cut"))
        self.horizontalLayout.addWidget(self.pushButton_cut)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listTracks = QtGui.QListView(self.verticalLayoutWidget)
        self.listTracks.setObjectName(_fromUtf8("listTracks"))
        self.verticalLayout.addWidget(self.listTracks)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pushButton_save = QtGui.QPushButton(self.verticalLayoutWidget)
        self.pushButton_save.setObjectName(_fromUtf8("pushButton_save"))
        self.horizontalLayout_2.addWidget(self.pushButton_save)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.formLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(0, 180, 321, 260))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setMargin(0)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label_titel = QtGui.QLabel(self.formLayoutWidget)
        self.label_titel.setObjectName(_fromUtf8("label_titel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_titel)
        self.lineEdit_titel = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEdit_titel.setObjectName(_fromUtf8("lineEdit_titel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.lineEdit_titel)
        self.label_artist = QtGui.QLabel(self.formLayoutWidget)
        self.label_artist.setObjectName(_fromUtf8("label_artist"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_artist)
        self.lineEdit_artist = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEdit_artist.setObjectName(_fromUtf8("lineEdit_artist"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.lineEdit_artist)
        self.label_album = QtGui.QLabel(self.formLayoutWidget)
        self.label_album.setObjectName(_fromUtf8("label_album"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_album)
        self.lineEdit_album = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEdit_album.setObjectName(_fromUtf8("lineEdit_album"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.lineEdit_album)
        self.label_genre = QtGui.QLabel(self.formLayoutWidget)
        self.label_genre.setObjectName(_fromUtf8("label_genre"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_genre)
        self.lineEdit_genre = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEdit_genre.setObjectName(_fromUtf8("lineEdit_genre"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.lineEdit_genre)
        self.label_kommentar = QtGui.QLabel(self.formLayoutWidget)
        self.label_kommentar.setObjectName(_fromUtf8("label_kommentar"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_kommentar)
        self.lineEdit_kommentar = QtGui.QLineEdit(self.formLayoutWidget)
        self.lineEdit_kommentar.setObjectName(_fromUtf8("lineEdit_kommentar"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.lineEdit_kommentar)
        self.label = QtGui.QLabel(self.formLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label)
        self.dateEdit = QtGui.QDateEdit(self.formLayoutWidget)
        self.dateEdit.setLocale(QtCore.QLocale(QtCore.QLocale.German, QtCore.QLocale.Germany))
        self.dateEdit.setMinimumDate(QtCore.QDate(2014, 1, 1))
        self.dateEdit.setObjectName(_fromUtf8("dateEdit"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.dateEdit)
        self.pushButton_change = QtGui.QPushButton(self.formLayoutWidget)
        self.pushButton_change.setObjectName(_fromUtf8("pushButton_change"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.pushButton_change)
        GodiRec.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(GodiRec)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 338, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuGodiRec = QtGui.QMenu(self.menubar)
        self.menuGodiRec.setObjectName(_fromUtf8("menuGodiRec"))
        GodiRec.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(GodiRec)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        GodiRec.setStatusBar(self.statusbar)
        self.actionExit = QtGui.QAction(GodiRec)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.menuGodiRec.addAction(self.actionExit)
        self.menubar.addAction(self.menuGodiRec.menuAction())

        self.retranslateUi(GodiRec)
        QtCore.QMetaObject.connectSlotsByName(GodiRec)

    def retranslateUi(self, GodiRec):
        GodiRec.setWindowTitle(_translate("GodiRec", "MainWindow", None))
        self.pushButton_play.setText(_translate("GodiRec", "Play", None))
        self.pushButton_stop.setText(_translate("GodiRec", "Stop", None))
        self.pushButton_rec.setText(_translate("GodiRec", "Rec", None))
        self.pushButton_cut.setText(_translate("GodiRec", "Cut", None))
        self.pushButton_save.setText(_translate("GodiRec", "Save", None))
        self.label_titel.setText(_translate("GodiRec", "Titel:", None))
        self.label_artist.setText(_translate("GodiRec", "Artist:", None))
        self.label_album.setText(_translate("GodiRec", "Album:", None))
        self.label_genre.setText(_translate("GodiRec", "Genre:", None))
        self.label_kommentar.setText(_translate("GodiRec", "Kommentar:", None))
        self.label.setText(_translate("GodiRec", "Jahr:", None))
        self.dateEdit.setDisplayFormat(_translate("GodiRec", "yyyy", None))
        self.pushButton_change.setText(_translate("GodiRec", "Change", None))
        self.menuGodiRec.setTitle(_translate("GodiRec", "File", None))
        self.actionExit.setText(_translate("GodiRec", "Exit", None))

