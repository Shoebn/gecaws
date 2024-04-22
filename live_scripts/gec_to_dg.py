from pathlib import Path
import shutil
import os
import datetime
import ftplib

def error_log(internal_code, e, directory):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()

    fromaddr = "dgreport@dgmarket.com"
    msg['Subject'] = 'GEC to DG Uploaded Files: ' + directory

    body = '<strong>' + internal_code + '</strong><br/>'
    body += str(e)
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "dgmarket@123")
    text = msg.as_string()
    toaddr = "jenil.a@globalecontent.com,shoeb.n@globalecontent.com,pooja.s@globalecontent.com,jitendar.j@globalecontent.com"
    msg['To'] = toaddr
    server.sendmail(fromaddr, toaddr.split(','), text)
    server.quit()

uploadedfiles = ''
filecount = 0
ftp_server = ftplib.FTP('ftp.dgmarket.com', 'scraperjson', 'Ghj,e;ltybe111')
ftp_server.encoding = "utf-8"
src = '/GeC/gecftp/uploaded_json'
directory = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
print(directory)
parent_dir = "/GeC/gecftp/DG_uploaded"
trg = os.path.join(parent_dir, directory) 
print(trg)
os.makedirs(trg) 
print("Directory '% s' created" % directory) 
folders=os.listdir(src)

for folder in folders:
    if folder != 'invalid_json':
        xml_files = os.path.join(src,folder)
        shutil.move(os.path.join(xml_files), trg)
filenames=os.listdir(trg)
try:
    for filename in filenames:
        uploadedfiles += filename
        uploadedfiles += '<br/>'
        filecount += 1
        filename2 = os.path.join(trg,filename)
        # with open(filename2, "rb") as file:
        #     ftp_server.storbinary(f"STOR {filename}", file)
    mailtext = 'Uploaded_Files: ' + str(filecount)
    mailtext2 = 'Data Uploading Failed: ' + str(filecount)
    error_log(mailtext, uploadedfiles, directory)
    print(mailtext)
except Exception as e:
    try:
        error_log(mailtext2, e, directory)        
    except:
        pass
    raise e
finally:
    ftp_server.quit()
