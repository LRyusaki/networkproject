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
        data = conn.recv(BUFSIZE)   # wait for client's COMMAND from user
        if data.endswith('exit'):   # if COMMAND 'exit'
            break                   # end, GO TO >>>print '> Done with', host, 'port', remoteport
        else:
            print '\t', host, '(%s): %s' % (remoteport,data)    # else not 'exit', show command to SERVER's SCREEN
            
            if data=='ls':          # if LS
                filelist = os.listdir(os.getcwd())  # get location from "os.getcwd()" and use "os.listdir()" to get filelist from that location
                for filename in filelist:           # each loop is 1 file on FILELIST keep in variable name 'filename'
                    data = '{:<30}'.format('\t'+filename)+'File Size: '+'{:>15,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB' # create information of that filename
                    conn.sendall(data)              # SEND the created information from before
                conn.sendall('END')                 # end FOR loop, send KEYWORD 'END'
        
            elif data.startswith('get '):           # if COMMAND start with 'get '
                filename = data[4:len(data)]        # seperate FILENAME from COMMAND
                if os.path.isfile(filename):        # if FILENAME exist
                    f = open(filename, 'rb')        # open file to read
                    for data in f:                  # read for each piece of DATA in file, 1 piece of data for 1 loop
                        conn.sendall(data)          # send piece of DATA
                    f.close()
                    conn.sendall('EndOfFiles')      # send KEYWORD to client to say end downloading
                else:
                    conn.sendall('File not found.') # there is no file, send KEYWORD
                        
            elif data.startswith('put '):           # if COMMAND start with 'put '
                filename = data[4:len(data)]        # separate filename from COMMAND 'put '
                f = open(filename, 'wb')            # create file to write
                conn.sendall('ready')               # send KEYWORD 'ready' for uploading
                while 1:                            # repeat receive data until end
                    data = conn.recv(BUFSIZE)       # receive 1 piece of data
                    if data.endswith('EndOfFiles'): # if found KEYWORD 'EndOfFiles', It's end of uploading
                        data = data[:-10]           # delete KEYWORD from data
                        f.write(data)               # write data to file
                        break
                    else:
                        f.write(data)               # write data to file
                f.close()

    print '> Done with', host, 'port', remoteport # break from "while 1:" came here
    conn.close()                # close SOCKET connection

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
            filelist = os.listdir(os.getcwd())  # get directory from "os.getcwd()" and use "os.listdir()" to get filelist from that directory
            for filename in filelist:           # each loop is 1 file on filelist keep in variable name 'filename'
                print '{:<30}'.format('\t'+filename)+'File Size: '+'{:>15,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB' # print information about that filename
    
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
                filename = str[4:len(str)]      # seperate FILENAME from COMMAND 'get ...'
                f = open(filename, 'wb')        # create file to write
                t1 = time.time()                # record start download time
                while 1:
                    if data.endswith('EndOfFiles'): # if download all of the file
                        data = data[:-10]           # delete KEYWORD
                        f.write(data)               # write the rest of file data
                        break
                    else:
                        f.write(data)               # write data to file
                    data = s.recv(BUFSIZE)          # get data from server
                t2 = time.time()                # record end download time
                f.close()                       # close file
                
                print '\tDownload file "'+filename+'" from server.'
                print '\tStatus: COMPLETED'
                print '\tFile Size: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0)+' KB'
                print '\tTransfer Time: '+'{:,.2f}'.format(t2-t1)+' s'
                print '\tDownload Throughput: '+'{:,.2f}'.format(os.stat(filename)[stat.ST_SIZE]/956.0/(t2-t1))+' KB/s'

        elif str.startswith('put '):        # command start with 'put '
            filename = str[4:len(str)]      # seperate FILENAME from COMMAND 'put ...'
            if os.path.isfile(filename):    # check if file exist
                s.send(str)                 # send COMMAND to server
                s.recv(BUFSIZE)             # get server 'READY to upload' status
                t1 = time.time()            # record start upload time
                f = open(filename, 'rb')    # open file to read
                for data in f:              # for each DATA in FILE
                    s.sendall(data)         # SEND that piece of file to SERVER
                f.close()
                t2 = time.time()            # record end upload time
                s.sendall('EndOfFiles')     # send end upload KEYWORD to server
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