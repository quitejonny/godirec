#!/usr/bin/env python
import os
import sys
import time
from PyQt4 import QtGui, QtCore
from godiRec import Recorder


class RecGui(QtGui.QWidget):

    exitFlag = 0

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.initUi()
        self.rec = Recorder(channels=2) 
        #with rec.open('nonblocking.wav', 'wb') as self.recfile2:

    def initUi(self):
        self.setWindowTitle('GodiRec')
        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)
        self.grid = QtGui.QGridLayout()
        hbox.addLayout(self.grid)
        spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Minimum)
        hbox.addItem(spacer)
        self.initRecUi()
        self.show()
        self.resize(550, 250)

    def initRecUi(self):
        self.btn_rec = QtGui.QPushButton("Rec", self)
        self.btn_play = QtGui.QPushButton("Play", self)
        self.btn_stop = QtGui.QPushButton("Stop", self)
        self.btn_save = QtGui.QPushButton("Save", self)
        self.btn_cut = QtGui.QPushButton("Cut", self)
        self.grid.addWidget(self.btn_rec, 1, 1)
        self.grid.addWidget(self.btn_play, 1, 2)
        self.grid.addWidget(self.btn_stop, 1, 3)
        self.grid.addWidget(self.btn_cut, 1, 4)
        self.grid.addWidget(self.btn_save, 2, 1)
        self.btn_rec.clicked.connect(self.buttonRec)
        self.btn_play.clicked.connect(self.buttonPlay)
        self.btn_stop.clicked.connect(self.buttonStop)
        self.btn_save.clicked.connect(self.buttonSave)
        self.btn_cut.clicked.connect(self.buttonCut)
        #self.btn_save.clicked.connect(self.buttonRec)
        
        self.table = QtGui.QTableWidget()
        self.table.setRowCount(1)
        self.table.setColumnCount(2)
        self.grid.addWidget(self.table, 2, 4)
        #self.grid.addWidget(self.led, 0, 0)
        self.grid.addWidget(self.table, 1, 0)
        self.table.setItem(1, 0, QtGui.QTableWidgetItem("test"))

    def buttonRec(self):
        if self.btn_rec.text() != "Recording":
            self.btn_rec.setText("Recording")
            self.btn_rec.setEnabled(False)
            self.btn_play.setText("Pause")
            self.btn_save.setEnabled(False)
            #self.recfile2.start_recording()                
            self.recfile = self.rec.open()
            self.recfile = self.recfile.start_recording()

    def buttonStop(self):
        self.btn_rec.setText("Rec")
        self.btn_rec.setEnabled(True)
        self.btn_play.setEnabled(True)
        self.btn_save.setEnabled(True)

    def buttonPlay(self):
        if self.btn_play.text() == "Pause":
            self.btn_play.setText("Play")
            self.btn_rec.setText("Rec")
            self.btn_rec.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.recfile.stop_recording()
        else:
            self.btn_play.setText("Pause")
            self.btn_rec.setText("Recording")
            self.btn_rec.setEnabled(False)
            self.recfile.start_recording()

    def buttonSave(self):
        self.rec.save("new.wav")

    def buttonCut(self):
        self.recfile.stop_recording()
        self.recfile.close()
        self.rec.save("track_1.mp3", ".temp/track_1.wav")
        self.recfile = self.rec.open()
        self.recfile.start_recording()


def run_gui():
    app = QtGui.QApplication(sys.argv)
    ex = RecGui()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
