import os
import re
import pandas as pd
import web_db_connection
from ScriptData import ScriptData

connection = web_db_connection.get_conn()
db_cursor = connection.cursor()
query = "select * from python_script_master"
db_cursor.execute(query)
db_results = db_cursor.fetchall()
connection.commit()
connection.close()

for single_script in db_results[1:]:
    notice_info = single_script[3].split('\n')
    dynamic_list = []
    static_list = []
    variables = ['urls','page_check','tender_html_element','next_page','lot_cpv_code','cpv_code','funding_agency','performance_country','performance_state','file_type','file_name','file_description','external_url','file_size','bidder_name','address','initial_estimated_value','final_estimated_value','bid_recieved','contract_duration','award_date','winner_group_name','grossawardvalueeuro','netawardvalueeuro','grossawardvaluelc','netawardvaluelc','award_quantity','notes','lot_criteria_title','lot_criteria_weight','lot_is_price_related','tender_criteria_title','tender_criteria_weight','tender_is_price_related','lot_actual_number','lot_number','lot_title','lot_description','lot_grossbudget','lot_netbudget','lot_grossbudget_lc','lot_netbudget_lc','lot_vat','lot_quantity','lot_min_quantity','lot_max_quantity','lot_quantity_uom','contract_number','contract_start_date','contract_end_date','lot_nuts','lot_is_canceled','lot_cancellation_date','lot_award_date','lot_cpvs','contract_typestr','lot_criteria','award_details','org_type','org_name','org_description','org_email','org_address','org_state','org_country','org_language','org_phone','org_fax','org_website','org_parent_id','org_city','customer_nuts','type_of_authority_code','customer_main_activity','postal_code','contact_person','tender_custom_tag_tender_id','tender_custom_tag_description','tender_custom_tag_value','tender_custom_tag_company_id','local_description','related_tender_id','notice_no','notice_title','main_language','est_amount','currency','procurement_method','eligibility','notice_deadline','publish_date','script_name','document_fee','completed_steps','crawled_at','additional_source_name','additional_source_id','additional_tender_url','dispatch_date','local_title','grossbudgeteuro','netbudgeteuro','grossbudgetlc','netbudgetlc','vat','document_type_description','type_of_procedure','type_of_procedure_actual','notice_summary_english','identifier','notice_type','cpvs','project_name','document_costfloat','earnest_money_depositstr','document_purchase_start_time','document_purchase_end_time','pre_bid_meeting_date','document_opening_time','notice_contract_type','source_of_funds','class_at_source','class_codes_at_source','class_title_at_source','bidding_response_method','notice_text','notice_url','category','funding_agencies','lot_details','custom_tags','customer_details','tender_criteria','attachments']

    for var in variables:
        for line in notice_info:
            script_data = ScriptData()
            script_data.line_id = notice_info.index(line) + 1
            script_data.internal_code = single_script[3].split('SCRIPT_NAME'.lower())[1].replace('=','').replace('"','').replace("'","").split('\n')[0].strip()
            script_data.dataid = '15097'
            line = line.replace('"','').replace("'","")
            if 'By.' in line and var in line:
                script_data.variable_name = var
                script_data.variable_elements = line.split('=')[1].split('.')[0].strip()
                script_data.variable_selector = line.split('By.')[1].split(',')[0].strip()
                if 'contains' in line:
                    script_data.variable_path = line.split('By.')[1].split(').')[0].replace('XPATH','').strip()
                else:
                    script_data.variable_path = line.split('By.')[1].split(',')[1].split(').')[0].strip()
            elif '# Onsite Field' in line:
                script_data.variable_name = line.split('# Onsite Field')[1]
                script_data.static_path = ''
                script_data.on_site = line
            elif '# Onsite Comment' in line:
                script_data.variable_name = line.split('# Onsite Comment')[1]
                script_data.static_path = ''
                script_data.on_site_comment = line
            else:
                if 'urls' in line and var in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.replace('urls','').replace('=','').replace('[','').replace(']','').strip()
                    except:
                        pass
                elif 'notice_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'lot_cpvs_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'cpvs_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'funding_agencies_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'performance_country_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'performance_state_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'attachments_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'award_details_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'lot_criteria_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'tender_criteria_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'lot_details_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'customer_details_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
                elif 'custom_tags_data.'+str(var) in line and 'By.' not in line:
                    script_data.variable_name = var
                    try:
                        script_data.static_path = line.split('=')[1].split('\n')[0].strip()
                    except:
                        pass
            
            clist = script_data.dataid, script_data.internal_code, script_data.variable_name,script_data.variable_elements,script_data.variable_selector,script_data.variable_path,script_data.static_path,script_data.on_site,script_data.on_site_comment,script_data.line_id
            if script_data.variable_selector != None:
                if clist not in dynamic_list:
                    dynamic_list.append(clist)
            if script_data.static_path != None:
                if clist not in static_list:
                    static_list.append(clist)
    
    for dynamic in dynamic_list:
        for i in range(len(static_list)):
            for static in static_list:
                if static[2] in dynamic[2]:
                    static_list.remove(static)
    dynamic_list.extend(static_list)

    connection = web_db_connection.get_conn()
    cursor = connection.cursor()
    for single_record in dynamic_list:
        cursor.execute("INSERT INTO script_generator_documents(script_generator_dataid, internal_code, variable_name, variable_elements,variable_selector,variable_path,static_path,on_site,on_site_comment,line_id)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (single_record[0], single_record[1], single_record[2], single_record[3],single_record[4],single_record[5],single_record[6],single_record[7],single_record[8],single_record[9]),)
    connection.commit()
    connection.close()
