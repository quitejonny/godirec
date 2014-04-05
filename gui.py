import os
import sys
import threading
from PyQt4 import QtGui, QtCore
from godiRec import GodiRec

class myThread (threading.Thread):
	def __init__(self, threadID, name, counter, rec):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter
		self.rec = rec
		print "in"
	def run(self):
		print "Starting " + self.name
		self.rec.recording()
		print "Exiting " + self.name

class RecGui(QtGui.QWidget):
	exitFlag = 0

	def __init__(self):
		super(RecGui, self).__init__()
		self.init_ui()
		self.rec = GodiRec() 

	def init_ui(self):
		self.setWindowTitle('GodiRec')
		hbox = QtGui.QHBoxLayout()
		self.setLayout(hbox)
		self.grid = QtGui.QGridLayout()
		hbox.addLayout(self.grid)
		spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding,
		                          QtGui.QSizePolicy.Minimum)
	        hbox.addItem(spacer)
	        self.init_rec_ui()
	        self.show()
	        self.resize(550, 250)
	
	def init_rec_ui(self):
		self.btn_rec = QtGui.QPushButton("Rec", self)
		self.btn_play = QtGui.QPushButton("Play", self)
		self.btn_stop = QtGui.QPushButton("Stop", self)
		self.btn_save = QtGui.QPushButton("Save", self)
                self.grid.addWidget(self.btn_rec, 1, 1)
		self.grid.addWidget(self.btn_play, 1, 2)
		self.grid.addWidget(self.btn_stop, 1, 3)
		self.grid.addWidget(self.btn_save, 2, 1)
		self.btn_rec.clicked.connect(self.buttonRec)
		self.btn_play.clicked.connect(self.buttonRec)
		self.btn_stop.clicked.connect(self.buttonRec)
		self.btn_save.clicked.connect(self.buttonRec)


	def buttonRec(self):
		self.btn_rec.setText("Recording")
		self.btn_rec.setEnabled(False)
		self.btn_play.setEnabled(False)
		self.btn_save.setEnabled(False)
		try:
			thread1 = myThread(1, "record", 1, self.rec)
			thread1.start()
		except:
			print "Unexpected error:", sys.exc_info()[0]

def run_gui():
	app = QtGui.QApplication(sys.argv)
	ex = RecGui()
	sys.exit(app.exec_())

if __name__ == "__main__":
	run_gui()
