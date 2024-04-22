import psycopg2


DATABASE_HOST = "prod-gec-db.chsqqj3urp6j.ap-south-1.rds.amazonaws.com"
DATABASE_NAME = "gecuserdb"
DATABASE_USERNAME = "gecpgadmin"
DATABASE_PASSWORD = "g3cStrongPass22"
DATABASE_PORT = "5432"

database = psycopg2.connect(user=DATABASE_USERNAME,
                      password=DATABASE_PASSWORD,
                      database=DATABASE_NAME,
                      host=DATABASE_HOST)
dbCursor = database.cursor()
sql = '''select iso2,name from countries '''

database.commit()
dbCursor.execute(sql)
allSourcesFromDB = dbCursor.fetchall()
allSources = []
for sourceFromDB in allSourcesFromDB:
    allSources.append(sourceFromDB[0])
script_name = (str(allSources).replace("[", "(").replace("]", ")"))


###============================================================
DATABASE_NAME2 = "global_content_db"

database2 = psycopg2.connect(user=DATABASE_USERNAME,
                      password=DATABASE_PASSWORD,
                      database=DATABASE_NAME2,
                      host=DATABASE_HOST)
dbCursor2 = database2.cursor()


sql2 = """select org_country,SUM(CASE WHEN notice_type != 7 THEN 1 ELSE 0 END) AS SPN_count, 
SUM(CASE WHEN notice_type = 7 THEN 1 ELSE 0 END) AS CA_count from  tender as t
	full join customer_details as c
	on t.posting_id = c.posting_id
WHERE
    DATE(update_date) = DATE(NOW()) - 1
    and is_publish_on_gec = True
GROUP BY
    org_country;
"""


    
    
# print(sql2)
database2.commit()
dbCursor2.execute(sql2)
sources_count = dbCursor2.fetchall()

sources_count
###============================================================
DATABASE_NAME3 = "global_content_db"

database3 = psycopg2.connect(user=DATABASE_USERNAME,
                      password=DATABASE_PASSWORD,
                      database=DATABASE_NAME3,
                      host=DATABASE_HOST)
dbCursor3 = database3.cursor()


sql3 = """SELECT
    count(distinct posting_id)
FROM
    tender
WHERE
    DATE(update_date) = DATE(NOW()) - 1 and is_publish_on_gec = True;
"""
# print(sql2)
database3.commit()
dbCursor3.execute(sql3)
total_download_count = dbCursor3.fetchall()

total_download_count[0][0]
###============================================================
# Create a dictionary to store values from list_two
dict_two = {}
for key, value in allSourcesFromDB:
    if key not in dict_two:
        dict_two[key] = []
    dict_two[key].append(value)

# Join the lists
result = []
for key, value, value2 in sources_count:
    if key in dict_two:
        for item in dict_two[key]:
            result.append((key, item, value,value2))
    else:
        # Add a tuple with blank status if the key doesn't exist in list_two
        result.append((key, 'None', value,value2))

# Add tuples for sources in list_two that don't exist in list_one with count as 0
for key, value in allSourcesFromDB:
    if key not in [x[0] for x in sources_count]:
        result.append((key, value, 0,0))

print(result)


###============================================================
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime

# Format the result list as an HTML table
table_html = "<table border='1'><tr><th>Country</th><th>Country Name</th><th>SPN Published on GeC</th><th>CA Published on GeC</th></tr>"
for row in result:
    table_html += "<tr>"
    for item in row:
        table_html += "<td>{}</td>".format(item)
    table_html += "</tr>"
table_html += "</table>"

# Construct the email message
msg = MIMEMultipart()
gladdr = "dgreport@dgmarket.com"
back_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
msg['Subject'] = 'GeC Country wise data Processed report for Date: ' + str(back_date)
#body = '<u><strong>GeC Sourcewise Count Report Dated: {}</strong></u><br/><br/>{}</br>'.format(back_date, table_html)

body = '<u><strong>GeC Countrywise Count Report Dated:</strong></u> ' + str(back_date) + '<br/><br/>' + '<u><strong>GeC total download count:</strong></u> ' + str(total_download_count[0][0]) + '<br/><br/>' + table_html


msg.attach(MIMEText(body, 'html'))
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(gladdr, "dgmarket@123")

text = msg.as_string()
#toaddr = "shoeb.n@globalecontent.com"
toaddr = "jenil.a@globalecontent.com,shoeb.n@globalecontent.com,pooja.s@globalecontent.com,jitendar.j@globalecontent.com,varun@globalecontent.com,prakash@globalecontent.com,akanksha@globalecontent.com"
msg['To'] = toaddr
server.sendmail(gladdr, toaddr.split(','), text)
server.quit()