#! /usr/bin/env python

# Test network throughput.
#
# Usage:
# 1) on SERVER: network -s [port]                    # start a server
# 2) on CLIENT: network -c [host] [port]             # start a client
#
# The server will service multiple clients until it is killed.
#
# The client performs one transfer of count*BUFSIZE bytes and
# measures the time it takes (roundtrip!).


import sys, time
import os
import stat
import thread
from socket import *

MY_PORT = 50042

BUFSIZE = 1024

def main():
    if len(sys.argv) < 2:   # if run only "python network.py" (have argument < 2)
        usage()             # load instruction how to run
    if sys.argv[1] == '-s': # if have "-s"
        server()            # run function server()
    elif sys.argv[1] == '-c':   # if have -c
        client()                # run function client()
    else:
        usage()


def usage():
    sys.stdout = sys.stderr
    print 'Server:      python network.py -s [port]'
    print 'Client:      python network.py -c [host] [port]'
    sys.exit(2)

def clientThread(conn, host, remoteport):
    while 1:
        data = conn.recv(BUFSIZE)
        if data.endswith('exit'):
            break
        else:
            print '\t', host, '(%s): %s' % (remoteport,data)
            
            if data=='ls':
                filelist = os.listdir(os.getcwd())
                for filename in filelist:
                    data = '{:<30}'.format('\t'+filename)+'File Size: '+'{:>15,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'
                    conn.sendall(data)
                conn.sendall('END')
        
            elif data.startswith('get '):
                filename = data[4:len(data)]
                if os.path.isfile(filename):
                    f = open(filename, 'rb')
                    for data in f:
                        conn.sendall(data)
                    f.close()
                    conn.sendall('EndOfFiles')
                else:
                    conn.sendall('File not found.')

            elif data.startswith('put '):
                filename = data[4:len(data)]
                f = open(filename, 'wb')
                conn.sendall('ready')
                while 1:
                    data = conn.recv(BUFSIZE)
                    if data.endswith('EndOfFiles'):
                        data = data[:-10]
                        f.write(data)
                        break
                    else:
                        f.write(data)
                f.close()

    print '> Done with', host, 'port', remoteport
    conn.close()

def server():
    if len(sys.argv) > 2:           # if have argument > 2, means have PORT
        port = eval(sys.argv[2])    # use input PORT
    else:
        port = MY_PORT              # else use default port

    s = socket(AF_INET, SOCK_STREAM)    # create socket with IPv4(INET) connection, socket type TCP(STREAM)
    host = getfqdn()                    # Get local machine name
    ip = gethostbyname(host)            # get ip from host name

    #   import urllib2
    #   my_ip = urllib2.urlopen('http://ip.42.pl/raw').read()

    s.bind((host, port))            # set IP and PORT to connect to this SOCKET
    s.listen(5)                     # maximum client
    print '\nHOST:            ', host
    print 'IP ADDRESS:      ', ip
    print 'PORT:            ', port, '\n'
    print '>>>> Server ready...'
    while 1:
        conn, (host, remoteport) = s.accept()   # when client connect, accept it as socket CONN
        print '> Client: %s(%s) connected.' % (host, remoteport)
        thread.start_new_thread(clientThread, (conn, host, remoteport)) # start new thread working with client that connect
    s.close()

def client():
    if len(sys.argv) < 3:       # if < 3 argument, no HOST no PORT
        usage()
    host = sys.argv[2]          # pass IF means, have HOST input from user
    ip = gethostbyname(host)    # get IP from HOST
    if len(sys.argv) > 3:       # if user give PORT
        port = eval(sys.argv[3])
    else:
        port = MY_PORT          # else use default PORT
    s = socket(AF_INET, SOCK_STREAM)    # create socket name 's'
    s.connect((host, port))     # connect to server's HOST, PORT from input
    print '\n\tConnect to SERVER'
    print 'HOST SERVER:            ', host
    print 'IP ADDRESS:      ', ip
    print 'PORT SERVER:            ', port, '\n'
    print '>>>> Client ready...'

    while 1:
        str = raw_input('>> '); # wait for command
        if str == 'lls':
            s.send(str) # send command to server
            filelist = os.listdir(os.getcwd())  #get directory from "os.getcwd()" and use "os.listdir()" to get filelist from that directory
            for filename in filelist:           # each loop is 1 file on filelist keep in variable name 'filename'
                print '{:<30}'.format('\t'+filename)+'File Size: '+'{:>15,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'         # print information about that filename
    
        elif str == 'ls':
            s.send(str) # send command to server
            while 1:
                data = s.recv(BUFSIZE)  # receive data from server (information about file)
                if data.endswith('END'): # data end with 'END'
                    print data[:-3]     # delete END and print
                    break
                else:
                    print data

        elif str.startswith('get '):    # command start with 'get '
            s.send(str)                 # send command to server
            data = s.recv(BUFSIZE)      # receive file status if found or not found
            if data.endswith('File not found.'):
                print data              # print 'file not found'
            else:                       # file found
                filename = str[4:len(str)]
                f = open(filename, 'wb')
                t1 = time.time()
                while 1:
                    if data.endswith('EndOfFiles'):
                        data = data[:-10]
                        f.write(data)
                        break
                    else:
                        f.write(data)
                    data = s.recv(BUFSIZE)
                t2 = time.time()
                f.close()
                
                print '\tDownload file "'+filename+'" from server.'
                print '\tStatus: COMPLETED'
                print '\tFile Size: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'
                print '\tTransfer Time: '+'{:,.2f}'.format(t2-t1)+' s'
                print '\tDownload Throughput: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0/(t2-t1))+' KB/s'

        elif str.startswith('put '):
            filename = str[4:len(str)]
            if os.path.isfile(filename):
                s.send(str)
                s.recv(BUFSIZE)
                t1 = time.time()
                f = open(filename, 'rb')
                for data in f:
                    s.sendall(data)
                f.close()
                t2 = time.time()
                s.sendall('EndOfFiles')
                print '\tUpload file "'+filename+'" to server.'
                print '\tStatus: COMPLETED'
                print '\tFile Size: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'
                print '\tTransfer Time: '+'{:,.2f}'.format(t2-t1)+' s'
                print '\tUpload Throughput: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0/(t2-t1))+' KB/s'
            else:
                print 'File not found.'

        elif str == 'exit':
            s.send(str)
            break

        else:
            print 'Error command given !'
            print '\tls - list files on server directory.'
            print '\tlls - list files on client directory.'
            print '\tget [filename] - download files from server.'
            print '\tput [filename] - upload files to server.'
            print '\texit - end connection.'
                
    print 'end'
    s.close()

main()