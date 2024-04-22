import boto3
import os,shutil
from datetime import date, datetime, timedelta
import gec_common.web_application_properties as application_properties

s3 = boto3.client(
    's3',
    aws_access_key_id = "AKIA2RUAKICYYAYSOO4I",
    aws_secret_access_key = "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"
)
folders = os.listdir(application_properties.NOTICE_ATTACHEMENTS_DIR)
print(folders)
for folder in folders:
    if folder != 'attachments_api':
        try:
            files = os.listdir(application_properties.NOTICE_ATTACHEMENTS_DIR+'/'+str(folder))
        except:
            print('NotADirectoryError: [Errno 20] Not a directory')
            continue
        m_time = os.path.getmtime(application_properties.NOTICE_ATTACHEMENTS_DIR+'/'+str(folder))
        dt_m = datetime.fromtimestamp(m_time)
        date_modified = str(dt_m).split(' ')[0]
        th = date.today() - timedelta(4)
        print(th)
        if str(date_modified) < str(th):
            print(True)
            for file in files:                
                s3.put_object(Bucket="gec-attachments", Key = folder+'/')
                s3.put_object_acl(ACL="public-read", Bucket='gec-attachments', Key = folder+'/')
                s3.upload_file(Filename = application_properties.NOTICE_ATTACHEMENTS_DIR+'/'+folder+'/'+file,Bucket = 'gec-attachments',Key = folder+'/'+file)
                s3.put_object_acl(ACL="public-read", Bucket='gec-attachments', Key = folder+'/'+file)
                os.remove(application_properties.NOTICE_ATTACHEMENTS_DIR+'/'+folder+'/'+file)
            shutil.rmtree(application_properties.NOTICE_ATTACHEMENTS_DIR+'/'+folder)
