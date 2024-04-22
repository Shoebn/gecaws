import web_db_connection
import datetime
import json
import os
import shutil
import gec_common.web_application_properties as application_properties
import logging
from gec_common import log_config
import jsonschema
from jsonschema import Draft7Validator,FormatChecker

def json_schema_validator():
    schema = json.loads(open("schema.json").read())
    validator = Draft7Validator(schema,format_checker=jsonschema.FormatChecker())

    json_File_path = application_properties.GENERATED_JSON_ROOT_DIR +'jsonfile'
    json_list = os.listdir(json_File_path)

    for filename in json_list:
        if '.json' in filename:
            print(filename)
            json_single_File = json_File_path +'/'+filename
            #print(json_single_File) 
            valid_json_file = application_properties.GENERATED_JSON_ROOT_DIR + 'jsonfile/validjson/' + filename 
            invalid_json_file = application_properties.GENERATED_JSON_ROOT_DIR + 'jsonfile/invalidjson/' + filename 

            with open('schema.json', 'r') as file:
                schema = json.load(file)

            try:
                with open(json_single_File) as f:
                    #print(json_single_File)
                    jsonData = json.load(f)
            except:
                shutil.move(json_single_File, application_properties.FAILED_JSON_DIR)
                continue
            valid_json = []
            invalid_json = []

            for records in jsonData:
                record = []
                record.append(records)
                if list(validator.iter_errors(record)) == []:
                    valid_json.append(records)
                    logging.info(list(validator.iter_errors(record)))

                else: 
                    invalid_json.append(records)
                    logging.info(list(validator.iter_errors(record)))            
            
            if valid_json != []:
                with open(valid_json_file, "w") as f:
                    json.dump(valid_json, f,indent = 6,sort_keys = True)
            
            if invalid_json != []:
                with open(invalid_json_file, "w") as f:
                    json.dump(invalid_json, f,indent = 6,sort_keys = True)
            os.remove(json_single_File)

json_schema_validator()    
connection = web_db_connection.get_conn()
cursor = connection.cursor()
json_File_path = application_properties.GENERATED_JSON_ROOT_DIR + 'jsonfile/validjson'
json_list = os.listdir(json_File_path)

for filename in json_list:
    json_single_File = json_File_path+'/'+filename
    logging.info(json_single_File)

    with open(json_single_File,'r') as single_File :
        json_data = json.load(single_File)

    #try:
    for record in json_data:
        json_object = json.dumps(record)
        json_object = json_object.replace("'","")
        query = "INSERT INTO json_import (json_text,file_name) VALUES ('"+str(json_object)+"','"+str(filename)+"' )"
        cursor.execute(query)
        connection.commit()
    try:
        shutil.move(json_single_File, application_properties.UPLOAD_JSON_DIR)
    except:
        json_single_File_new = json_File_path+'/'+'already_exist_'+filename
        os.rename(json_single_File, json_single_File_new)
        shutil.move(json_single_File_new, application_properties.UPLOAD_JSON_DIR)
        pass
    #except Exception as e:
    #    logging.info("Exception in FAILED_JSON_DIR: {}".format(e))
    #    shutil.move(json_single_File, application_properties.FAILED_JSON_DIR)
    #    pass
###################################
invalid_json_file = application_properties.GENERATED_JSON_ROOT_DIR + 'jsonfile/invalidjson'
invalid_json_list = os.listdir(invalid_json_file)

for filename in invalid_json_list:

    json_single_File = invalid_json_file +'/'+filename
    logging.info(json_single_File)

    with open(json_single_File,'r') as single_File :
        json_data = json.load(single_File)

    #try:
    for record in json_data:
        json_object = json.dumps(record)
        json_object = json_object.replace("'","")
        query = "INSERT INTO json_import (json_text,file_name,is_posted) VALUES ('"+str(json_object)+"','"+str(filename)+"' ,'False')"
        cursor.execute(query)
        connection.commit()
    try:
        shutil.move(json_single_File, application_properties.UPLOAD_JSON_DIR +'/invalid_json')
        print("moved")
    except:
        json_single_File_new = json_File_path+'/'+'already_exist_'+filename
        os.rename(json_single_File, json_single_File_new)
        shutil.move(json_single_File_new, application_properties.UPLOAD_JSON_DIR+'/invalid_json')
        print("except moved")
        pass
    #except Exception as e:
    #    logging.info("Exception in FAILED_JSON_DIR: {}".format(e))
    #    shutil.move(json_single_File, application_properties.FAILED_JSON_DIR)
    #    pass

connection.close()
