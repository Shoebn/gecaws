import web_db_connection
import datetime
import json
import gec_common.web_application_properties as application_properties
import logging
from pathlib import Path
import shutil
import os
import ftplib

def error_log(internal_code, e, directory):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()

    fromaddr = "shoeb.n@dgmarket.in"
    msg['Subject'] = 'Uploaded Files: ' + directory

    body = '<strong>' + internal_code + '</strong><br/>'
    body += str(e)
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "Amyr@123")
    text = msg.as_string()
    toaddr = "jitendar.j@globalecontent.com,shoeb.n@globalecontent.com"
    msg['To'] = toaddr
    server.sendmail(fromaddr, toaddr.split(','), text)
    server.quit()
    
def directory_exists(dir):
    filelist = []
    ftp_server.retrlines('LIST',filelist.append)
    for f in filelist:
        if f.split()[-1] == dir and f.upper().startswith('D'):
            return True
    return False

def chdir(dir): 
    if directory_exists(dir) is False: # (or negate, whatever you prefer for readability)
        ftp_server.mkd(dir)
    ftp_server.cwd(dir)
    
uploadedfiles = ''
filecount = 0
# ftp_server = ftplib.FTP('ftp.dgmarket.com', 'cuberm', 'HxWxD2.50')
# ftp_server.encoding = "utf-8"
# ftp_server.cwd('CubeRM_POC/Tenders') 
# print(ftp_server.retrlines('LIST'))
src = 'C:\\Users\\Administrator\\Documents\\cubeRM_output\\validjson'
directory = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
parent_dir = "C:\\Users\\Administrator\\Documents\\cuberm uploaded"
trg = os.path.join(parent_dir, directory) 
print(trg)
os.makedirs(trg) 
print("Directory '% s' created" % directory) 
folders=os.listdir(src)

for folder in folders:
    xml_files = os.path.join(src,folder)
    shutil.move(os.path.join(xml_files), trg)
filenames=os.listdir(trg)

uploadedfiles = ''
filecount = 0
# try:
for file in filenames:
    ftp_server = ftplib.FTP('ftp.dgmarket.com', 'cuberm', 'HxWxD2.50')
    ftp_server.encoding = "utf-8"
    ftp_server.cwd('CubeRM_POC/Tenders') 
    m_time = os.path.getmtime(trg+'/'+str(file))
    dt_m = datetime.datetime.fromtimestamp(m_time)
    date_modified = str(dt_m).split(' ')[0]
    country = file.split('_')[0]
    sitename = file.split('_')[1]
    chdir(country)
    chdir(sitename)
    chdir(date_modified)

    uploadedfiles += file
    uploadedfiles += '<br/>'
    filecount += 1
    filename2 = os.path.join(trg,file)
    print(filename2)
    if file.startswith(country):
        with open(filename2, "rb") as filee:
            ftp_server.storbinary(f"STOR {file}", filee)
        mailtext = 'Uploaded_Files: ' + str(filecount)
        mailtext2 = 'Data Uploading Failed: ' + str(filecount)
    ftp_server.quit()