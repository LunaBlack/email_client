#/usr/bin/python
# -*- coding: utf-8 -*-


import re, os
import socket
import ssl
from email.mime.text import MIMEText
from email.utils import formatdate
from email.base64mime import encode as encode_base64

CRLF = "\r\n" #define crlf


class SMTPException(Exception): #define exception class
    pass

class SMTPServerDisconnected(SMTPException):
    pass

class SMTPResponseException(SMTPException):
    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

        
class MyEmailClient():

    def __init__(self): #instantiate socket
        self.file = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

    def user_input(self): #user input informations of mail
        self.username = raw_input('user_id:')
        self.password = raw_input('password:')
        self.host = raw_input('server_host:')
        self.port = raw_input('server_port:')
        self.fro = raw_input('email_from:')
        
        self.to = raw_input('email_to:')
        self.sub = raw_input('subject:')
        self.text_path = raw_input('the path of text:') #the text contains contents of the e-mail
        

    def write_mail(self): #instantiate and define MIMEText
        self.msg = MIMEText(self.getcontent(self.text_path), 'plain', 'utf-8')
        self.msg['From'] = self.fro
        self.msg['Subject'] = self.sub
        self.msg['To'] = self.to
        self.msg['Date'] = formatdate(localtime=True) 


    def getcontent(self, path): #get mail content from text
        f = os.path.abspath(path)
        content = open(f, 'rb')
        data = content.read()
        try:
            data = data.decode('gbk')
        except:
            data = data.decode('gbk','ignore')
        content.close()
        return data


    def quotedata(self, data): #quote mail data by regular expression
        return re.sub(r'(?m)^\.', '..', re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data))

        
    def putcmd(self, cmd, args=''): #socket send
        if args == '':
            string = '%s%s' % (cmd, CRLF)
        else:
            string = '%s %s%s' % (cmd, args, CRLF)
        try:
            self.sock.sendall(string)
        except socket.error:
            raise SMTPServerDisconnected('Server not connected')


    def getreply(self): #socket receive
        resp = []
        if self.file is None:
            self.file = self.sock.makefile('rb')
        while 1:
            try:
                line = self.file.readline()
            except socket.error as e:
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed: " + str(e))
            if line == '':
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed")

            resp.append(line[4:].strip())
            code = line[:3]
            try:
                errcode = int(code)
            except ValueError:
                errcode = -1
                break
            if line[3:4] != '-':
                break

        errmsg = "\n".join(resp)
        return (errcode, errmsg)


    def connect(self): #socket connect
        host = self.host
        port = int(self.port)
        addr = (host, port)
        
        self.sock.connect(addr)
        (code, msg) = self.getreply()
        if not (200 <= code <=299):
            raise SMTPServerDisconnected('Server not connected')
        
        return (code, msg)
    

    def helo(self): #send helo command
        self.putcmd('helo', self.host)
        (code, msg) = self.getreply()
        if not (200 <= code <=299):
            raise SMTPResponseException(code, resp)
        return (code, msg)
    

    def ehlo(self): #send ehlo command
        self.putcmd('ehlo', self.host)
        (code, msg) = self.getreply()

        if code == -1 and len(msg) == 0:
            self.close()
            raise SMTPServerDisconnected("Server not connected")
        if code != 250:
            raise SMTPResponseException(code, resp)

        return (code, msg)

    
    def starttls(self): #put the connection to the SMTP server into TLS mode
        self.putcmd('starttls')
        (code, msg) = self.getreply()
        if code != 220:
            raise SMTPResponseException(code, msg)
        else:
            self.sock = ssl.wrap_socket(self.sock) #wrap socket
            self.file = SSLFakeFile(self.sock) #ssl-readline, ssl-send
        return (code, msg)

    
    def login(self): #log in on the SMTP server
        self.putcmd('auth login')
        (code, msg) = self.getreply()
        if code != 334:
            raise SMTPResponseException(code, msg)

        self.putcmd(encode_base64(self.username, eol=''))
        (code, msg) = self.getreply()
        if code != 334:
            raise SMTPResponseException(code, msg)
        
        self.putcmd(encode_base64(self.password, eol=''))
        (code, msg) = self.getreply()
        if code not in (235, 503):
            # 235 == 'Authentication successful'
            # 503 == 'Error: already authenticated'
            raise SMTPResponseException(code, msg)
        return (code, msg)


    def send_mail(self): #a complete process of SMTP protocol
        self.write_mail()
        self.connect()
        self.helo()
        self.ehlo()
        self.starttls()
        self.ehlo()
        self.login()

        self.putcmd('mail', "FROM:%s" % self.msg['From']) #send mail command
        (code, msg) = self.getreply()
        if code != 250:
            raise SMTPResponseException(code, msg)

        self.putcmd('rcpt', "TO:%s" % self.msg['To']) #send rcpt command
        (code, msg) = self.getreply()
        if code != 250:
            raise SMTPResponseException(code, msg)

        self.putcmd('data') #send data command
        (code, msg) = self.getreply()
        if code != 354:
            raise SMTPResponseException(code, msg)
        
        else:
            data = self.quotedata(self.msg.as_string())
            if data[-2:] != CRLF:
                data = data + CRLF
            data = data + '.' + CRLF
            
            self.sock.sendall(data)
            (code, msg) = self.getreply()
            if code != 250:
                raise SMTPResponseException(code, msg)
            
            print "succeed to send email"
            return True
        

    def close(self): #close socket connection
        if self.file:
            self.file.close()
        self.file = None
        if self.sock:
            self.sock.close()
        self.sock = None


    def quit(self): #terminate the SMTP session
        self.putcmd('quit')
        self.close()
        return True


class SSLFakeFile: #wrap a SSLObject
    
    def __init__(self, sslobj):
        self.sslobj = sslobj

    def readline(self): #ssl-readline
        str = ""
        chr = None
        while chr != "\n":
            chr = self.sslobj.read(1)
            if not chr:
                break
            str += chr
        return str

    def send(self, str): #ssl-send
        self.sslobj.send(str)

    def close(self):
        pass

    
if __name__ == '__main__':
    my_email = MyEmailClient()
    my_email.user_input()
    my_email.send_mail()
    my_email.quit()
