import sys
from PyQt4 import QtCore, QtGui,Qt
from qplayer_ui import * 
from res_rc import *
from connection import *

class Player(QtGui.QMainWindow):
	def __init__(self,parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui=Ui_MainWindow()
		self.ui.setupUi(self)
		self.ui.treeWidget.setColumnWidth(0,17)
		self.ui.treeWidget.setHeaderLabel("#")
		self.ui.treeWidget_2.setHeaderLabel("Artists / Albums / Tracks")
		self.firststart=True
		self.mute=False

		self.play=False
		self.plItem=None
		#stworzenie watku
		self.connection=Connection(self)
		self.pupd=ProgressUpdate(self)
		#podlaczenie sygnalu z watku do funkcji
		QtCore.QObject.connect(self.connection,QtCore.SIGNAL("get_status()"), self.loadData)
		QtCore.QObject.connect(self.pupd.timer,QtCore.SIGNAL("timeout()"), self.updateBar)
		QtCore.QObject.connect(self.connection,QtCore.SIGNAL("change_song()"), self.changeSong)
		QtCore.QObject.connect(self.connection,QtCore.SIGNAL("change_playlist()"), self.loadPlaylist)
		QtCore.QObject.connect(self.connection,QtCore.SIGNAL("playback_error()"), self.playbackError)

		#tu bedzie wiecej podlaczen... zapewne
		#odpalenie watku
		self.connection.start()
		self.pupd.start()
	
	def databaseFill(self):
			for item in self.loaddtb.items:
				self.ui.treeWidget_2.addTopLevelItem(item)
			self.ui.treeWidget_2.sortItems(0,0)
							
	def updateBar(self,force=False):
		if force:
			try:
				status=self.connection.call('status')
				try:
					pr=str(status['time']).split(":")
					pr[1]
				except:
					#worst line ever?
					
					ti=self.connection.call('playlistinfo')[int(status['songid'])]
					pr=[0,ti['time']]
					
				self.ui.progressBar.setMaximum(int(pr[1]))
				self.ui.progressBar.setValue(int(pr[0]))
				self.ui.progressBar.setFormat(str(int(pr[0])//60).zfill(2)+":"+str(int(pr[0])%60).zfill(2))
			except:
				pass
		elif not force and self.play:
			#try:
				self.ui.progressBar.setValue(int(self.ui.progressBar.value())+1)
				t=self.ui.progressBar.text()
				m,s=str(t).split(":")
				m=int(m)
				s=int(s)
				if s==59:
					s=0
					m=m+1
				else:
					s=s+1
					
					
				self.ui.progressBar.setFormat(str(m).zfill(2)+":"+str(s).zfill(2))
			#except:
			#	pass

		
	
	def loadData(self):
		'''funkcja do ladowania informacji na starcie programu'''
		#pobranie statusu i ustawienie ikonki
		status=self.connection.call('status')
		state=str(status['state'])
	


		if  state== 'pause' or state== 'stop':
			self.play=False
			try: 
				self.pupd.timer.stop()
			except: pass

		elif not state=='processing':
			self.play=True
			self.pupd.timer.start()


		#pobranie nazwy artysty
		current=self.connection.call('currentsong')
		title,artist,album=self.getTags(current)
		song=artist+" - "+title
		time=self.getTime(current)
		self.status=StatusInfo(self.ui.statusbar,song,time,'')
		self.setWindowTitle(song)
		self.setPlayPauseBtn()

		#pobranie volume... TODO: ustawienie vol w mpd podzielnego przez 5
		vol=int(status['volume'])//5
		self.ui.volSlider.setValue(vol)
		self.getVolIcon()
		if self.play:
			self.updateBar(True)
		else:
			self.ui.progressBar.setMaximum(200)
			self.ui.progressBar.setValue(0)
			self.ui.progressBar.setFormat("00:00")
		self.loadPlaylist()
		if self.firststart:
			self.loaddtb=LoadDatabase(self,self.connection.call('listallinfo'))
			QtCore.QObject.connect(self.loaddtb,QtCore.SIGNAL("add_item()"), self.databaseFill)
			self.loaddtb.start()
		self.firststart=False
		
	def loadPlaylist(self):
		self.ui.treeWidget.clear()
		#ladowanie playlisty:
		for track in self.connection.call('playlistinfo'):
			title,artist,album=self.getTags(track)
			item=QtGui.QTreeWidgetItem([" ",str(int(track['pos'])+1),artist,title,album,track['file'].split("/")[-1],track['file']])
			self.ui.treeWidget.addTopLevelItem(item)
		self.highlightTrack()
		
	def changeSong(self):
		current=self.connection.currentsong
		title,artist,album=self.getTags(current)
		song=artist+" - "+title
		self.status.setTrack(song)
		self.status.setTime(self.getTime(current))
		self.updateBar(True)
		self.highlightTrack()
		self.setWindowTitle(song)


	@QtCore.pyqtSlot()
	def on_playBtn_clicked(self):
		if self.play:
			self.status.setPlaying("Paused")
			self.play=False

			self.connection.pause(1)
			self.pupd.timer.stop()
			self.updateBar(True)		


		else:
			self.play=True
			self.pupd.timer.start()
			self.connection.play()
			self.updateBar(True)

		self.setPlayPauseBtn()



	@QtCore.pyqtSlot()
	def on_nextBtn_clicked(self):
		if not self.play:
			self.connection.play()
			self.play=True
			self.pupd.timer.start()
			self.setPlayPauseBtn()
	
		self.connection.next()
		self.updateBar(True)

	@QtCore.pyqtSlot()
	def on_prevBtn_clicked(self):

		if not self.play:
			self.connection.play()
			self.play=True
			self.pupd.timer.start()
			self.setPlayPauseBtn()

		self.connection.previous()
		self.updateBar(True)


	def on_stopBtn_clicked(self):
		self.connection.stop()

		self.play=False
		self.setPlayPauseBtn()

		self.pupd.timer.stop()

		self.status.setPlaying("Stop")
		self.ui.progressBar.setMaximum(200)
		self.ui.progressBar.setValue(0)
		self.ui.progressBar.setFormat("00:00")



	@QtCore.pyqtSlot()
	def on_volImg_clicked(self):
		icon=QtGui.QIcon()
		if self.mute:
			self.getVolIcon()
			self.mute=False
			vol=self.vol*5
			self.connection.call('setvol',vol)
		else:
			icon.addPixmap(QtGui.QPixmap(":/icons/audio-volume-muted.png"))
			self.mute=True
			self.vol=int(self.connection.status['volume'])//5
			self.connection.call('setvol',0)
			
			self.ui.volImg.setIcon(icon)
	def on_volSlider_valueChanged(self,a):
		if not self.mute: self.getVolIcon()
		volume=str(self.ui.volSlider.value()*5)
		self.ui.volSlider.setToolTip("Volume:"+volume)
		self.connection.call('setvol',volume)
		self.status.setVolume(volume)
		self.vol=volume
		
	def getVolIcon(self):
		icon=QtGui.QIcon()
		val=self.ui.volSlider.value()
		if val>15: vol="high"
		elif val<=15 and val>5: vol="medium"
		elif val<=5 and val>1: vol="low"
		else: vol="muted"
		icon.addPixmap(QtGui.QPixmap(":/icons/audio-volume-"+vol+".png"))
		self.ui.volImg.setIcon(icon)
	def highlightTrack(self):
		try:
			item=self.ui.treeWidget.topLevelItem(int(self.connection.call('currentsong')['pos']))
			item.setText(0,"#")

		except: item=None
	
		try:
			self.plItem.setText(0,"")

		except: pass
		self.plItem=item

	def on_treeWidget_itemActivated(self,e):
		nr=e.text(1)
		self.connection.play(int(nr)-1)
		self.play=True
		self.pupd.timer.start()
		self.setPlayPauseBtn()
	def on_treeWidget_2_itemActivated(self,e):
		if e.childCount()==0:
			filename=e.text(1)
			self.connection.call('add',filename)
		else:
			for i in range(e.childCount()):
				item=e.child(i)
				if not e.parent():
					for j in range(item.childCount()):
						self.connection.call('add',item.child(j).text(1))
				else:
					self.connection.call('add',item.text(1))
		self.status.showMessage(e.text(0)+" added to playlist")		
				
	
	def setPlayPauseBtn(self):
		icon=QtGui.QIcon()
		if self.play:
			self.status.setPlaying("Play")

			icon.addPixmap(QtGui.QPixmap(":/icons/media-playback-pause.png"))
		else:
			icon.addPixmap(QtGui.QPixmap(":/icons/media-playback-start.png"))
		self.ui.playBtn.setIcon(icon)

	def getTags(self,track):
			try: artist=track['artist']
			except: artist=""
			try: title=track['title']
			except: title=""
			try: album=track['album']
			except: album=""
			if artist=="" and title=="": 
				try: title=track['file'].split("/")[-1]
				except: title="--"
			return title,artist,album
	def getTime(self,track):
		try:
			time=int(track['time'])
			time=str(time//60).zfill(2)+":"+str(time%60).zfill(2)

		except:
			time="00:00"

		return time
			
	def playbackError(self):
		self.play=False
		self.pupd.timer.stop()
		self.setPlayPauseBtn()
		self.status.setPlaying("Stop")
class StatusInfo(object):
	
	def __init__(self,statusbar,track,time,playing):
		self.statusbar=statusbar
		self.track=track
		self.time=time
		self.playing=playing
		self.timer=QtCore.QTimer()
		self.timer.setInterval(5000)
		self.decorator="   --==::==--   "
		QtCore.QObject.connect(self.timer,QtCore.SIGNAL("timeout()"), self.setStatus)
		self.setStatus()
	def setStatus(self):
		status=self.decorator+self.playing+" || "+self.track+" || "+self.time+self.decorator
		self.statusbar.showMessage(status)
	def showMessage(self,message):
		status=self.decorator+self.playing+" || "+self.track+" || "+self.time+self.decorator
		self.statusbar.showMessage(status+message) 
		self.timer.singleShot(5000,self.setStatus)
	def setTime(self,x):
		self.time=x
		self.setStatus()
	def setVolume(self,x):
		self.volume=x
		self.setStatus()		
	def setTrack(self,x):
		self.track=x
		self.setStatus()
	def setPlaying(self,x):
		self.playing=x
		self.setStatus()
	
class ProgressUpdate(QtCore.QThread):
	def __init__(self,parent):
		super(ProgressUpdate,self).__init__(parent)		
		self.parent=parent
		self.timer=QtCore.QTimer()
		
	def run(self):
		self.timer.setInterval(1000)
			

		

if __name__=="__main__":
	app= QtGui.QApplication(sys.argv)
	myapp = Player()
	myapp.show()
	sys.exit(app.exec_())
