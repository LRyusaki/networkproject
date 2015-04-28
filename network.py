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
    if len(sys.argv) < 2:
        usage()
    if sys.argv[1] == '-s':
        server()
    elif sys.argv[1] == '-c':
        client()
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
    if len(sys.argv) > 2:
        port = eval(sys.argv[2])
    else:
        port = MY_PORT

    s = socket(AF_INET, SOCK_STREAM)
    host = getfqdn() # Get local machine name
    ip = gethostbyname(host)

    #   import urllib2
    #   my_ip = urllib2.urlopen('http://ip.42.pl/raw').read()

    s.bind((host, port))
    s.listen(5)
    print '\nHOST:            ', host
    print 'IP ADDRESS:      ', ip
    print 'PORT:            ', port, '\n'
    print '>>>> Server ready...'
    while 1:
        conn, (host, remoteport) = s.accept()
        print '> Client: %s(%s) connected.' % (host, remoteport)
        thread.start_new_thread(clientThread, (conn, host, remoteport))
    s.close()

def client():
    if len(sys.argv) < 3:
        usage()
    host = sys.argv[2]
    ip = gethostbyname(host)
    if len(sys.argv) > 3:
        port = eval(sys.argv[3])
    else:
        port = MY_PORT
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((host, port))
    print '\n\tConnect to SERVER'
    print 'HOST SERVER:            ', host
    print 'IP ADDRESS:      ', ip
    print 'PORT SERVER:            ', port, '\n'
    print '>>>> Client ready...'

    while 1:
        str = raw_input('>> ');
        if str == 'lls':
            s.send(str)
            filelist = os.listdir(os.getcwd())
            for filename in filelist:
                print '{:<30}'.format('\t'+filename)+'File Size: '+'{:>15,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'
    
        elif str == 'ls':
            s.send(str)
            while 1:
                data = s.recv(BUFSIZE)
                if data.endswith('END'):
                    print data[:-3]
                    break
                else:
                    print data

        elif str.startswith('get '):
            s.send(str)
            data = s.recv(BUFSIZE)
            if data.endswith('File not found.'):
                print data
            else:
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