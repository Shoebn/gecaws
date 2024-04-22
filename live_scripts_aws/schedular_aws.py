import db_connect
connection = db_connect.con()
cursor = connection.cursor()

result_new = []

query = """select replace(replace(replace(json_build_object(region_aws,replace(replace(replace(JSON_AGG(json_build_object('script_name',	internal_code,'scheduled_time',scheduled_time,'server',case when instance_name = 1 then 'Windows' else 'Linux' end):: text) ::text, '\',''), '}"','}'), '"{','{'))::text, '\',''), ']"',']'), '"[','[')
 as schedular
from app_sources where status in (1,13) and region_aws is not null
group by region_aws """
cursor.execute(query)
results = cursor.fetchall()

for result in results:
    result2 = str(result[0]).replace("\\\\\\", "")
    result_new.append(result2)

result_new2 = (str(result_new).replace("'", "")) 
file1 = open("schedular_aws.json","w")
file1.write(result_new2)
file1.close() 

