import mpd
from PyQt4 import QtCore,QtGui

class Connection(QtCore.QThread):
	def __init__(self,parent):
		super(Connection,self).__init__(parent)		
	def run(self):
		PASSWORD = False
		self.client = mpd.MPDClient()
		self.client.connect("localhost", 6600)
		if PASSWORD:
			try:
				client.password(PASSWORD)
			except CommandError:
				exit(1)
		self.status=self.call('status')
		#po pobraniu info wysyla sygnal
		self.emit(QtCore.SIGNAL("get_status()"),)
		self.sleep(1)
		self.running=True
		self.currentsong=self.call('currentsong')
		self.currentplaylist=self.call('playlist')
		self.state=self.call('status')['state']
		

		while self.running:
			self.sleep(1)
			self.status=self.call('status')
			if self.currentsong!=self.call('currentsong'):
				#self.sleep(0.1)
				self.currentsong=self.call('currentsong')
				self.emit(QtCore.SIGNAL("change_song()"),)
				#self.sleep(1)
			if self.currentplaylist!=self.call('playlist'):
				self.currentplaylist=self.call('playlist')
				self.emit(QtCore.SIGNAL("change_playlist()"),)
				#self.sleep(1)
			try:
				if self.state!=self.call('status')['state']:
					#self.sleep(1)
					self.state=self.call('status')['state']
					self.emit(QtCore.SIGNAL("get_status()"),)
			except:pass
	
	def error(self,err_nr):
		if err_nr==1:
			self.emit(QtCore.SIGNAL("playback_error()"),)

	def play(self,id=None):
		if id==None:
			self.call('play')
		else: self.call('play',id)
		if self.call('status')['state']!="play": self.error(1)
	def pause(self,*arg):
		self.call('pause',*arg)
		if self.call('status')['state']!="pause": self.error(1)		

	def stop(self):
		self.call('stop')
		if self.call('status')['state']!="stop": self.error(1)	
	def previous(self):
		self.call('previous')
		if self.call('status')['state']!="play": self.error(1)							

	def next(self):
		self.call('next')
		if self.call('status')['state']!="play": self.error(1)		
	def call(self,cmd,*args):
		if cmd=='status':
			value=getattr(self.client,cmd)(*args)
			if value and 'state' in value:
				return value
			else: 
				return {'state':'processing'}
		else:
			try:
				value=getattr(self.client,cmd)(*args)
			except: 
					value=None
			return value
class LoadDatabase(QtCore.QThread):
	def __init__(self,parent,listall):
		super(LoadDatabase,self).__init__(parent)
		self.listall=listall
		self.parent=parent		
	def run(self):	
		self.items=[]
		artists=[]
		#albums=[]
		albums={}
		#albums={'Unknown artist':{'Unknown album':[]}
		for i in self.listall:
			try:
				artist=i['artist']
			except:
				artist=".Unknown artist"
			try:
				track=[i['title'],i['file']]
			except:
				try:
					track=[i['file'],i['file']]
				except:
					track="$$5dir5$$"	
			try:	
				album=i['album']
			except: 
				album=".Unknown album"
			if track!="$$5dir5$$":
				#if not artist in album: albums[artist]=[]
				try:albums[artist]
				except KeyError:albums[artist]={}
				if 	albums[artist].has_key(album):
					albums[artist][album].append(track)
				else :
					albums[artist][album]=[track]


		#print albums
		for i in albums:
			item=QtGui.QTreeWidgetItem([str(i)])
			for j in albums[i]:
				child=QtGui.QTreeWidgetItem([str(j)])
				item.addChild(child)
				for k in albums[i][j]:
					grandchild=QtGui.QTreeWidgetItem(k)
					child.addChild(grandchild)
		
			self.items.append(item)
		#print i,j,k
	
		self.emit(QtCore.SIGNAL("add_item()"),)
