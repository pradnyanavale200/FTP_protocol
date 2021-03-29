import sys, string, pam, subprocess, os
from struct import *
from socket import *
from thread import *


def createConnSocket():
	try:
		global serverConnPort
		global serverConnSocket 
		serverConnSocket = socket(AF_INET,SOCK_STREAM)
	except error, msg:
		print 'Can\'t connect: '+ msg[1]

def bindConnSocket():
	try:
		global serverConnPort
		global serverConnSocket
		serverConnPort = 2202
		serverConnSocket.bind(('',serverConnPort))
		serverConnSocket.listen(10)
	except error, msg:
		print 'Can\'t connect: '+ msg[1]
		bindConnSocket()

def createDataSocket():
	try:
		global dataPort
		global dataSocket 
		dataSocket = socket(AF_INET,SOCK_STREAM)
	except error, msg:
		print 'Can\'t connect: '+ msg[1]

def bindDataSocket():
	try:
		global dataPort
		global dataSocket
		dataPort = 2203
		dataSocket.bind(('',dataPort))
		dataSocket.listen(10)
	except error, msg:
		print 'Can\'t connect: '+ msg[1]
		bindDataSocket()

def connSocket_accept():
	global conn
	global addr
	conn, addr = serverConnSocket.accept()
	

def perm(filename):
	with open(filename,'rb') as f:
		try:
			l = f.read(1024)
			msg = '226'
		except:
			msg = '550'
	return msg
	
def get(filename, dataConn):
	with open(filename,'rb') as f:
		l = f.read(1024)
		while (l):
			dataConn.send(l)
			l = f.read(1024)

def put(filename, dataConn):
	with open(filename,'wb') as f:
		while True:
			data = dataConn.recv(1024)
			if not data:
				break
			f.write(data)

def dataConn_accept(sock):
	dataConn, dataAddr = sock.accept()
	return dataConn
	

def clientThread(conn, sock):
	
	flag = 0
	hostname = gethostname()
	conn.send(hostname.encode())
	name = conn.recv(65565).decode()
	msg = '331 Please specify the password.'
	conn.send(msg.encode())
	password = conn.recv(65565).decode()
	p = pam.pam()
	check = p.authenticate(name, password)
	if check == True:
		msg = '230 Login successful.'
		conn.send(msg.encode())
	else:
		msg = '530 Login incorrect.\nLogin failed.'
		conn.send(msg.encode())
		conn.close()
	if check == True:
		while True:
			cmd = conn.recv(65565).decode()
			cmdlist = list(cmd.split())
	
			if cmdlist[0] == 'bye' or cmdlist[0] == 'exit' or cmdlist[0] == 'quit':
				try:	
					msg = '221 Goodbye.'	
					conn.send(msg.encode())
					conn.close()
				except error, msg:
					pass		
				break

			elif cmdlist[0] == 'close' or cmdlist[0] == 'disconnect':
				try:	
					msg = '221 Goodbye.'	
					conn.send(msg.encode())
					conn.close()
				except error, msg:
					pass
				break

			elif cmdlist[0] == 'get' or cmdlist[0] == 'recv':
				if len(cmdlist) == 1:
					rfilename = conn.recv(1024).decode()
				else:
					filenames = list(cmdlist[1:])
					rfilename = filenames[0]
				dataConn = dataConn_accept(sock)
				if os.path.exists(rfilename):
					msg = '150 Opening BINARY mode data connection for '+ rfilename
					flag = 1
				else:
					msg = '550 Failed to open file.'
					flag = 0
				conn.send(msg.encode())
				msg = conn.recv(1024).decode()
				if flag == 1:
					get(rfilename, dataConn)
					msg = 'Transfered!'
					conn.send(msg.encode())
				dataConn.close()


			elif cmdlist[0] == 'put' or cmdlist[0] == 'send':
				if len(cmdlist) == 1:
					rfilename = conn.recv(1024).decode()
				else:
					filenames = list(cmdlist[1:])
					if len(filenames) > 1:
						rfilename = filenames[1]
					else:
						rfilename = filenames[0]
				dataConn = dataConn_accept(sock)
				msg = conn.recv(1024).decode()
				if msg == '1':
					put(rfilename, dataConn)
					
				dataConn.close()


			elif cmdlist[0] == 'mget':
				if len(cmdlist) == 1:
					filenames = list(conn.recv(1024).decode().split())
				else:
					filenames = list(cmdlist[1:])
				i = 0
				n = len(filenames)
				while i < n:
					filename = filenames[i]
					if os.path.exists(filename):
						chck = '1'
						conn.send(chck.encode())
					else:
						chck = '0'
						conn.send(chck.encode())
						i = i + 1
						continue
					query = conn.recv(1).decode()
					if query == 'y':
						dataConn = dataConn_accept(sock)
						msg = perm(filename)
						conn.send(msg.encode())
						if msg == '226':
							get(filename, dataConn)
						dataConn.close()
					else:
						i = i + 1
						continue
					i = i + 1

			elif cmdlist[0] == 'mdelete':
				if len(cmdlist) == 1:
					filenames = list(conn.recv(1024).decode().split())
				else:
					filenames = list(cmdlist[1:])
				msg = '#'
				conn.send(msg.encode())
				i = 0
				n = len(filenames)
				while i < n:
					filename = filenames[i]
					if conn.recv(1).decode() == 'y':
						if(os.path.exists(filename)):
							os.remove(filename)
							data = 'file removed!'
						else:
							data = 'file not found'	
						conn.send(data.encode())
					else:
						continue
					i = i + 1

			elif cmdlist[0] == 'mdir':
				if len(cmdlist) == 1:
					filenames = list(conn.recv(1024).decode().split())
				else:
					filenames = list(cmdlist[1:])
				msg = '#'
				conn.send(msg.encode())
				n = len(filenames) - 1
				dirnames = filenames[0:n]
				query = conn.recv(1).decode()
				if query == 'y':
					for dirname in dirnames:
						if os.path.isdir(dirname):
							lst = list(os.listdir(dirname))
							data = ' '
							for i in lst:
								data = data + '\n' + i
						else:
							data = ' '
						conn.send(data.encode())
					

			elif cmdlist[0] == 'mput':
				if len(cmdlist) == 1:
					filenames = list(conn.recv(1024).decode().split())
				else:
					filenames = list(cmdlist[1:])
				i = 0
				n = len(filenames)
				while i < n:
					filename = filenames[i]
					chck = conn.recv(1).decode()
					if chck == '0':
						i = i + 1
						continue
					query = conn.recv(1).decode()
					if query != 'y' :
						i = i + 1
						continue
					msg = conn.recv(3).decode()
					dataConn = dataConn_accept(sock)
					if msg == '226':
						put(filename, dataConn)
					dataConn.close()
					i = i + 1
			
			elif cmdlist[0] == 'size':
				filename = cmdlist[1]
				if(os.path.exists(filename)):
					data = os.path.getsize(filename)
					data = str(data) + 'B'
				else:
					data = 'file not found!'
				conn.send(data.encode())
			elif cmdlist[0] == 'rmdir':
				dirname = cmdlist[1]
				if(os.path.exists(dirname)):
					shutil.rmtree(dirname)
					data = 'directory successfully removed!'
				else:
					data = 'directory not found!'
				conn.send(data.encode())
		
			elif cmdlist[0] == 'delete':
				filename = cmdlist[1]
				if(os.path.exists(filename)):
					os.remove(filename)
					data = 'file removed!'
				else:
					data = 'file not found'	
				conn.send(data.encode())
		
		
			elif cmdlist[0] == 'rename':
				filenames = list(cmdlist[1:])
				src = filenames[0]
				dest = filenames[1]
				if(os.path.exists(src)):
					os.rename(src, dest)
					data = 'file succesfully renamed!'
				else:
					data = 'file not found!'
				conn.send(data.encode())



			elif cmdlist[0][0] == '!':
				pass

			elif cmdlist[0] == 'lcd':
				pass
		
			elif cmdlist[0] == 'pwd':
				curr = os.getcwd()
				conn.send(curr.encode())

			elif cmdlist[0] == 'cd':
				passMsg = '250 Directory successfully changed.'
				failMsg = '550 Failed to change directory'
				if len(cmdlist) == 1:
					dirname = conn.recv(1024).decode()
				elif len(cmd) > 2:
					dirname = cmdlist[1]		
				curr = os.getcwd()
				path = os.path.join(curr, dirname)
				if os.path.isdir(path):
					os.chdir(path)
					conn.send(passMsg.encode())
				else:
					conn.send(failMsg.encode())
			
			elif cmdlist[0] == 'cdup':
				curr = os.getcwd()
				os.path.abspath(os.path.join(curr, os.pardir))
				msg = '250 Directory successfully changed'
			

			elif cmdlist[0] == 'ls':
				curr = os.getcwd()
				filenames = list(os.listdir(curr))
				data = ''
				for i in filenames:
					data = data + i + '\n'
				conn.send(data.encode())


			elif cmdlist[0] == 'dir':
				if len(cmdlist) == 1:
					curr = os.getcwd()
					filenames = list(os.listdir(curr))
					data = ' '
					for i in filenames:
						data = data + i + '\n'
					conn.send(data.encode())
				else:
					dirname = cmdlist[1]
					if os.path.exists(dirname):
						filenames = list(os.listdir(dirname))
						data = ' '
						for i in filenames:
							data = data + i + '\n'
						conn.send(data.encode())
					else:
						data = ''
						conn.send(data.encode())

			elif cmdlist[0] == 'mkdir':
				passMsg = '250 Directory successfully created.'
				failMsg = '550 Permission denied'
				if len(cmdlist) == 1:
					dirname = conn.recv(1024).decode()
				elif len(cmdlist) > 1:
					dirname = cmdlist[1]
				flag = 1
				try:
					os.mkdir(dirname)
				except:
					flag = 0
				if flag != 0:
					conn.send(passMsg.encode())
				else:
					conn.send(failMsg.encode())		
			

			else:
				msg = '?Invalid command'
				query = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
				out_byte = query.communicate()
				output = out_byte[0].decode("utf-8")
				if out_byte[1].decode("utf-8") == '':
					conn.send(output.encode())
				else:
					conn.send(msg.encode())
		



createConnSocket()
bindConnSocket()
createDataSocket()
bindDataSocket()
global connSocket
global conn
global dataSocket
while True:
	connSocket_accept()
	start_new_thread(clientThread, (conn, dataSocket,))
	
	
			
