import web_db_connection
import datetime
import json
import os
import shutil
import gec_common.web_application_properties as application_properties
import logging
import jsonschema
from jsonschema import Draft7Validator

def json_schema_validator():
    schema = json.loads(open("cube_schema.json").read())
    validator = Draft7Validator(schema)

    json_File_path = application_properties.GENERATED_JSON_ROOT_DIR +'cubeRM_output'
    json_list = os.listdir(json_File_path)

    for filename in json_list:
        if '.json' in filename:
            print(filename)
            json_single_File = json_File_path +'/'+filename
            #print(json_single_File) 
            valid_json_file = application_properties.GENERATED_JSON_ROOT_DIR + 'cubeRM_output/validjson/' + filename 
            invalid_json_file = application_properties.GENERATED_JSON_ROOT_DIR + 'cubeRM_output/invalidjson/' + filename 

            with open('cube_schema.json', 'r') as file:
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
