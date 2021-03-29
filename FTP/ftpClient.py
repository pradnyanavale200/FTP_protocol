import sys, string, getpass
from struct import *
from socket import *
import subprocess, os

def createSocket():
	sock = socket(AF_INET, SOCK_STREAM)
	return sock

def socketConnect(sock, servername, port):
	try:
		sock.connect((servername, port))
		flag = 1
	except error, msg:
		print 'ftp: connect: Connection refused: ' +msg[1]
		flag = 0
	return flag

def get(filename, dataSocket):
	with open(filename,'wb') as f:
		while True:
			data = dataSocket.recv(1024)
			if not data:
				break
			f.write(data)	
		

def perm(filename):
	with open(filename,'rb') as f:
		try:
			l = f.read(1024)
			msg = '226'
		except:
			msg = '550'
	return msg

def put(lfilename, dataSocket):
	with open(lfilename,'rb') as f:
		l = f.read(1024)
		while (l):
			dataSocket.send(l)
			l = f.read(1024)

def not_connect():
	cmd = raw_input('ftp> ')
	cmdlist = list(cmd.split())
	if cmdlist[0][0] == '!':
		msg = '+bash :' + cmd + ': Command not found.'
		query = subprocess.Popen(cmd[1:], shell = True, stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
		out_byte = query.communicate()
		if out_byte[1].decode("utf-8") == '':
			output = out_byte[0].decode("utf-8")
			print output
		else:
			print msg

	elif cmdlist[0] == 'bye' or cmdlist[0] == 'exit' or cmdlist[0] == 'quit':
		
		sys.exit()
	
	elif cmdlist[0] == 'close':
		print 'Not connected.'
		
	elif cmdlist[0] == 'lcd':
		if len(cmdlist) > 1:
			dirs = list(cmdlist[1:])
			if len(dirs) > 1:
				print 'usage: lcd local-directory'
			else:
				dirname = dirs[0]
				curr = os.getcwd()
				path = os.path.join(curr, dirname)
				if os.path.isdir(path):
					os.chdir(path)
					print 'Local directory now ' +os.getcwd()
				else:
					print 'local: ' + dirname + ': No such file or directory'
		else:
			print 'Local directory now' +os.getcwd()

	else:
		print 'Not connected.'
	
if len(sys.argv) == 2:
	serverName = sys.argv[1]
	port = 2202
	dataPort = 2203
elif len(sys.argv) > 2:
	serverName = sys.argv[1]
	port = int(sys.argv[2])
	dataPort = port + 1
if len(sys.argv) >= 2:
	prompt = 1
	clientSocket = createSocket()

	flag = socketConnect(clientSocket, serverName, port)
	
	if flag == 1:
		hostName = clientSocket.recv(65565).decode()
		print 'Connected to ' + serverName + '.'
		sys.stdout.write('Name (' + serverName + ':' + hostName + '):')
		name = raw_input()
		clientSocket.send(name.encode())
		msg = clientSocket.recv(65565).decode()
		print msg
		password = getpass.getpass(prompt = 'Password:', stream = None)
		clientSocket.send(password.encode())
		msg = clientSocket.recv(65565).decode()
		print msg
		if msg[0:3] == '230':
			flagg = 1
		else:
			flagg = 0
	if flagg == 1:
		while True:
			try:
				cmd = raw_input('ftp> ')
			except KeyboardInterrupt:
				print ' '
				continue
			except:
				continue
			cmdlist = list(cmd.split())
			try:
				clientSocket.send(cmd.encode())
			except error, msg:
				pass
			if cmdlist[0] == 'bye' or cmdlist[0] == 'exit' or cmdlist[0] == 'quit':
				try:	
					msg = clientSocket.recv(1024).decode()	
					print msg	
					clientSocket.close()
				except error, msg:
					pass		
				sys.exit()
	
			elif cmdlist[0] == 'close' or cmdlist[0] == 'disconnect':
				try:	
					msg = clientSocket.recv(1024).decode()	
					print msg	
					clientSocket.close()
				except error, msg:
					print 'Not connected.'
					pass
		
			elif cmdlist[0] == 'prompt':
				if prompt == 1:
					prompt = 0
					print 'Interactive mode off.'
				else:
					prompt = 1
					print 'Interactive mode on.'		

			elif cmdlist[0] == 'mput' and flagg == 1:
				if len(cmdlist) == 1:
					filenames = raw_input('(local-file) ')
					clientSocket.send(filenames.encode())
					msgs = clientSocket.recv(1024).decode()
					filenames = list(filenames.split())
				else:
					filenames = list(cmdlist[1:])
				i = 0
				n = len(filenames)
				while i < n:
					filename = filenames[i]
					if os.path.exists(filename):
						chck = '1'
						clientSocket.send(chck.encode())
					else:
						chck = '0'
						clientSocket.send(chck.encode())
						i = i + 1
						continue
					if prompt == 1:
						msg = 'mput ' + filenames[i] + '? ' 
						query = raw_input(msg)
						if query.lower() != 'yes' and query.lower() != 'y':
							query = 'n'
							clientSocket.send(query.encode())
							i = i + 1
							continue
						else:
							query = 'y'
							clientSocket.send(query.encode())
					else:
						query = 'y'
						clientSocket.send(query.encode())
					dataSocket = createSocket()
					flag = socketConnect(dataSocket, serverName, dataPort)
					if flag == 1:
						msg = perm(filename)
						clientSocket.send(msg.encode())
						if msg == '226':
							put(filename, dataSocket)
							print '226 Transfer complete'
						else:
							print '550 Permission denied'
						dataSocket.close()
					else:
						print 'Not connected'
						break
					i = i + 1

				
	
			elif cmdlist[0] == 'mget' and flagg == 1:
				if len(cmdlist) == 1:
					remotefile = raw_input('(remote-file) ')
					clientSocket.send(remotefile.encode())
					remotefile = list(remotefile.split())
				else:
					filenames = list(cmdlist[1:])
				i = 0
				n = len(remotefile)
				while i < n:
					chck = clientSocket.recv(1).decode()
					if chck == '0':
						i = i + 1
						continue
					if prompt == 1:
						msg = 'mget ' + filenames[i] + '? ' 
						query = raw_input(msg)
						if query.lower() != 'yes' and query.lower() != 'y':
							query = 'n'
							clientSocket.send(query.encode())
							i = i + 1
							continue
						else:
							query = 'y'
							clientSocket.send(query.encode())
					else:
						query = 'y'
						clientSocket.send(query.encode())

					dataSocket = createSocket()
					flag = socketConnect(dataSocket, serverName, dataPort)
					if flag == 1:
						filename = filenames[i]
						msg = clientSocket.recv(3).decode()
						if msg == '226':
				
							get(filename, dataSocket)
							print '226 Transfer complete'
						else:
							print '550 Permission denied'
					dataSocket.close()
					i = i + 1


			elif (cmdlist[0] == 'put' or cmdlist[0] == 'send') and flagg == 1:
				if len(cmdlist) == 1:
					lfilename = raw_input('(local-file) ')
					rfilename = raw_input('(remote-file) ')
					rfilename = list(rfilename.split())
					rfilename = rfilename[0]
					clientSocket.send(rfilename.encode())
					lfilename = list(lfilename.split())
					lfilename = lfilename[0]
				else:
					filenames = list(cmdlist[1:])		
					if len(filenames) > 1:
						lfilename = filenames[0]
						rfilename = filenames[1]
					else:
						rfilename = filenames[0]
						lfilename = filenames[0]
				print 'local: ' + lfilename + ' remote: ' + rfilename
				dataSocket = createSocket()
				flag = socketConnect(dataSocket, serverName, dataPort)
				if flag == 1:
					if os.path.exists(lfilename):
						msg = '1'
						clientSocket.send(msg.encode())
						msg = put(lfilename, dataSocket)
						print msg
				dataSocket.close()
	

			elif (cmdlist[0] == 'get' or cmdlist[0] == 'recv') and flagg == 1:
				if len(cmdlist) == 1:
					rfilename = raw_input('(remote-file) ')
					lfilename = raw_input('(local-file) ')
					rfilename = list(rfilename.split())
					rfilename = rfilename[0]
					clientSocket.send(rfilename.encode())
					lfilename = list(lfilename.split())
					lfilename = lfilename[0]
				else:
					filenames = list(cmdlist[1:])		
					if len(filenames) > 1:
						lfilename = filenames[1]
						rfilename = filenames[0]
					else:
						rfilename = filenames[0]
						lfilename = filenames[0]
				print 'local: ' + lfilename + ' remote: ' + rfilename
				dataSocket = createSocket()
				flag = socketConnect(dataSocket, serverName, dataPort)
				if flag == 1:
					msg = clientSocket.recv(1024).decode()
					print msg
					clientSocket.send(msg.encode())
					if msg[0:3] == '150':
						get(lfilename, dataSocket)
						msg = clientSocket.recv(1024).decode()
						print msg
				dataSocket.close()

		
			elif cmdlist[0] == 'lcd':
				if len(cmdlist) > 1:
					dirs = list(cmdlist[1:])
					if len(dirs) > 1:
						print 'usage: lcd local-directory'
					else:
						dirname = dirs[0]
						curr = os.getcwd()
						path = os.path.join(curr, dirname)
						if os.path.isdir(path):
							os.chdir(path)
							print 'Local directory now ' +os.getcwd()
						else:
							print 'local: ' + dirname + ': No such file or directory'
				else:
					print 'Local directory now' +os.getcwd()
	
			elif cmdlist[0] == 'pwd' and flagg == 1:
				curr = clientSocket.recv(1024).decode()
				print curr	
		
			elif cmdlist[0] == 'cd' and flagg == 1:	
				if len(cmdlist) == 1:
					dirname = raw_input('(remote.directory) ')
					clientSocket.send(dirname.encode())
				msg = clientSocket.recv(1024)
				print msg

			elif cmdlist[0] == 'mkdir' and flagg == 1:	
				if len(cmdlist) == 1:
					dirname = raw_input('(directory-name) ')
					clientSocket.send(dirname)
				msg = clientSocket.recv(1024)
				print msg
				
	
			elif len(cmdlist) == 1 and cmdlist[0] == 'ls' and flagg == 1:
				curr = clientSocket.recv(65565)
				print curr

			elif cmdlist[0] == 'dir' and flagg == 1:
				curr = clientSocket.recv(65565).decode()
				print '200 PORT command successful. Consider using PASV.'
				print '150 Here comes the directory listing.'
				print curr 
				print '226 Directory send OK'

			elif cmdlist[0] == 'mdir':
				if len(cmdlist) == 1:
					filenames = raw_input('(remote-file) ')
					clientSocket.send(filenames.encode())
					filenames = list(filenames.split())
				else:
					filenames = list(cmdlist[1:])
				n = len(filenames) - 1
				filename = filenames[0:n]
				lfile = filenames[n]
				print lfile
				msg = clientSocket.recv(1).decode()
				if prompt == 1:
					msg = 'output to local-file:  ' + lfile + '? ' 
					query = raw_input(msg)
					if query.lower() == 'yes' or query.lower() == 'y':
						query = 'y'			
					else:
						query = 'n'
				else:
					query = 'y'
				clientSocket.send(query.encode())
				if query == 'y':				
					fp = open(lfile, 'wb+')
					for fn in filename:
						curr = clientSocket.recv(1024).decode()
						print '200 PORT command successful. Consider using PASV.'
						print '150 Here comes the directory listing.'
						fp.write(curr) 
						print '226 Directory send OK'
					fp.close()

			elif cmdlist[0] == 'rename':
				curr = clientSocket.recv(1024).decode()
				print curr

			elif cmdlist[0] == 'size':
				curr = clientSocket.recv(1024).decode()
				print curr
		
			elif cmdlist[0] == 'delete':
				curr = clientSocket.recv(1024).decode()
				print curr
	
			elif cmdlist[0] == 'cdup':
				curr = clientSocket.recv(1024).decode()
				print curr

			elif cmdlist[0] == 'mdelete':
				if len(cmdlist) == 1:
					filenames = raw_input('(remote-file) ')
					clientSocket.send(filenames.encode())
					filenames = list(filenames.split())
				else:
					filenames = list(cmdlist[1:])
				msg = clientSocket.recv(1).decode()
				for filename in filenames:
					if prompt == 1:
						msg = 'mdelete ' + filename + '? ' 
						query = raw_input(msg)
						if query.lower() == 'yes' and query.lower() == 'y':
							query = 'y'						
						else:
							query = 'n'
							clientSocket.send(query.encode())
							i = i + 1
							continue
					else:
						query = 'y'
					clientSocket.send(query.encode())					
					curr = clientSocket.recv(1024).decode()
					print curr


			elif cmdlist[0] == 'rmdir':
				curr = clientSocket.recv(1024).decode()
				print curr
					
		
			elif cmdlist[0][0] == '!':
				msg = '+bash :' + cmd + ': Command not found'
				query = subprocess.Popen(cmd[1:], shell = True, stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
				out_byte = query.communicate()
				if out_byte[1].decode("utf-8") == '':
					output = out_byte[0].decode("utf-8")
					print output
				else:
					print msg
	
			elif flagg == 1:
				data = clientSocket.recv(65565).decode()
				print data
	
			else:
				print 'Not connected.'


	else:
		while True:
			not_connect()

else:
	while True:
		not_connect()
