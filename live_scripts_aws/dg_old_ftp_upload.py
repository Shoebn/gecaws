from pathlib import Path
import shutil
import os
import datetime
import ftplib
import gec_common.web_application_properties as application_properties
from datetime import datetime

# Define the folder path
output_folder = application_properties.GENERATED_JSON_ROOT_DIR + "/" + "DG_OLD_OUTPUT"

UPLOADED_DIR =  application_properties.GENERATED_JSON_ROOT_DIR + "/" +  "DG_OLD_OUTPUT_UPLOADED" 

def error_log(internal_code, e, directory):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()

    fromaddr = "dgreport@dgmarket.com"
    msg['Subject'] = 'Uploaded Files: ' + directory

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
ftp_server = ftplib.FTP('ftp.dgmarket.com', 'tahmid', 'AHKIVC45DG')
ftp_server.encoding = "utf-8"
ftp_server.cwd('tender247')  
directory = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
print(directory)
if not os.path.exists(UPLOADED_DIR):
    os.makedirs(UPLOADED_DIR)

trg = os.path.join(UPLOADED_DIR, directory) 
print(trg)
os.makedirs(trg) 
print("Directory '% s' created" % directory) 
xml_file=os.listdir(output_folder)
for file in xml_file:
    shutil.move(os.path.join(output_folder,file), trg)
filenames=os.listdir(trg)
try:
    for filename in filenames:
        uploadedfiles += filename
        uploadedfiles += '<br/>'
        filecount += 1
        filename2 = os.path.join(trg,filename)
        with open(filename2, "rb") as file:
            ftp_server.storbinary(f"STOR {filename}", file)
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
