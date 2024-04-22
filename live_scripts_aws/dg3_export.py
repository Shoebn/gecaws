import jsons
import web_db_connection
import datetime
import json,shutil
from gec_common.cube_class import *
import gec_common.OutputXML
from datetime import date, datetime, timedelta
from gec_common import web_application_properties as application_properties
import sys

#todaydate = sys.argv[1]#2023-10-25
#todaytime = sys.argv[2]#17:53
#yesterdaydate = sys.argv[3]#2023-10-24
#yesterdaytime = sys.argv[4]#17:53

def today_formatted():
    return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

# def json_import(json_File):
connection = web_db_connection.get_conn()
cursor = connection.cursor()

today = date.today() 
# today_date = '2023-10-25 17:53:24.579819'
today_date = datetime.now()
#today_date = todaydate +' '+todaytime + ':00.000000'

query_yesterday = "select TO_CHAR(max(created_time),'YYYY-MM-DD HH24:MI:SS.FF6') from dgmarket_export_log"
cursor.execute(query_yesterday)
yesterday_date = cursor.fetchall()
# yesterday_date = [('2023-10-24 17:53:24.579819',),]
#yesterday_date = yesterdaydate +' '+yesterdaytime + ':00.000000'
#yesterday_date = [(yesterday_date,),]

sql = """select distinct script_name from tender where update_date between """
query = sql + "'" + str(yesterday_date[0][0]) + "'" + " and " + "'" +  str(today_date) + "'"
cursor.execute(query)


# Fetch the results from the cursor object
script_names = cursor.fetchall()
for script_name in script_names:    
    notice_count = 0
    output_xml_file = gec_common.OutputXML.OutputXML(str(script_name[0]))
    sql2 = """select distinct posting_id from tender where is_publish_on_gec is true and (completed_steps != 'deleted' or completed_steps is null) and update_date between"""
    query2 = sql2 + "'"+ str(yesterday_date[0][0]) + "'" + " and " + "'" + str(today_date) + "'" + " and script_name = '"  + str(script_name[0]) + "'"
    cursor.execute(query2)
    posting_ids =  cursor.fetchall()
    dgmarket_export_log_query = "INSERT INTO dgmarket_export_log (posting_ids,created_time) VALUES ('"+str(posting_ids)+"','"+str(today_date)+"')"
    cursor.execute(dgmarket_export_log_query)
    connection.commit()
    for posting_id in posting_ids:
        sql3 = """SELECT 
	XMLELEMENT(NAME Notice, 
		XMLELEMENT(NAME notice_id, posting_id),
		XMLELEMENT(NAME notice_no,notice_no),
		XMLELEMENT(NAME notice_title,notice_title),
		XMLELEMENT(NAME  main_language,main_language),
	XMLELEMENT(NAME performance_country, (select performance_country from performance_country where posting_id = """+ str(posting_id[0]) +"""
	 LIMIT 1)),
	XMLELEMENT(NAME city, (select performance_state from performance_state where posting_id = """+ str(posting_id[0]) +"""
	 LIMIT 1)),	
	XMLELEMENT(NAME notice_type, CASE
		when notice_type::text = '0'  then 	'others'
		when notice_type::text = '1'  then 	'pn'	
		when notice_type::text = '2'  then 	'gpn'	
		when notice_type::text = '3'  then 	'pp'	
		when notice_type::text = '4'  then 	'spn'	
		when notice_type::text = '5'  then 	'rei'	
		when notice_type::text = '6'  then 	'ppn'	
		when notice_type::text = '7'  then 	'ca'	
		when notice_type::text = '8'  then 	'rfc'	
		when notice_type::text = '9'  then 	'anc'	
		when notice_type::text = '10' then  'prj'	
		when notice_type::text = '11' then  'vc'	
		when notice_type::text = '12' then  'grn'	
		when notice_type::text = '13' then  'acq'	
		when notice_type::text = '14' then  'mrg'	
		when notice_type::text = '15' then  'rpt'	
		when notice_type::text = '16' then  'amd'
		else 'others'
	end ),
	XMLELEMENT(NAME procurement_method, case 
		when procurement_method::text = '2' then 'Other'
		when procurement_method::text = '0' then 'National Competitive Bidding(NCB)'
		when procurement_method::text = '1' then 'International Competitive Bidding (ICB)'
	end ),
		XMLELEMENT(NAME est_amount , est_amount),
		XMLELEMENT(NAME currency , currency), 
		XMLELEMENT(NAME qualification, eligibility),
		XMLELEMENT(NAME notice_deadline , notice_deadline),
		XMLELEMENT(NAME publish_date , publish_date),
		XMLELEMENT(NAME notice_source, script_name ), 
		XMLELEMENT(NAME document_fee , document_fee),
		XMLELEMENT(NAME completed_steps , completed_steps),
		XMLELEMENT(NAME official_text, notice_text ),
		XMLELEMENT(NAME external_url, notice_url ),
		XMLELEMENT(NAME notice_summary, concat('notice_summary_english: ', notice_summary_english, 
	' crawled_at : ', crawled_at , 
	' additional_source_name: ', additional_source_name, 
	' additional_source_id: ', additional_source_id, 
	' additional_tender_url: ', additional_tender_url, 
	' dispatch_date: ', dispatch_date, 
	' local_title: ', local_title, 
	' grossbudgeteuro: ', grossbudgeteuro, 
	' netbudgeteuro: ', netbudgeteuro, 
	' grossbudgetlc: ', grossbudgetlc, 
	' netbudgetlc: ', netbudgetlc, 
	' vat: ', vat, 
	' document_type_description: ', document_type_description, 
	' type_of_procedure: ', type_of_procedure, 
	' type_of_procedure_actual: ', type_of_procedure_actual, 
	' identifier: ', identifier, 
	' contract_duration: ', contract_duration, 
	' project_name: ', project_name, 
	' document_cost: ', document_cost, 
	' earnest_money_deposit: ', earnest_money_deposit, 
	' document_purchase_start_time: ', document_purchase_start_time, 
	' document_purchase_end_time: ', document_purchase_end_time, 
	' pre_bid_meeting_date: ', pre_bid_meeting_date, 
	' document_opening_time: ', document_opening_time, 
	' notice_contract_type: ', notice_contract_type, 
	' source_of_funds: ', source_of_funds, 
	' class_at_source: ', class_at_source, 
	' class_codes_at_source: ', class_codes_at_source, 
	' class_title_at_source: ', class_title_at_source, 
	' bidding_response_method: ', bidding_response_method, 
	' category: ', category, 
	' tender_cancellation_date: ', tender_cancellation_date, 
	' tender_contract_end_date: ', tender_contract_end_date, 
	' tender_contract_start_date: ', tender_contract_start_date, 
	' tender_contract_number: ', tender_contract_number, 
	' tender_is_canceled: ', tender_is_canceled, 
	' tender_award_date: ', tender_award_date, 
	' tender_min_quantity: ', tender_min_quantity, 
	' tender_max_quantity: ', tender_max_quantity, 
	' tender_quantity_uom: ', tender_quantity_uom
	) ),
	( SELECT 
    xmlagg(XMLELEMENT(NAME notice_documents, 
		XMLELEMENT(NAME id, id),
      	XMLELEMENT(NAME file_size, file_size),
      	XMLELEMENT(NAME file_type, file_type), 
      	XMLELEMENT(NAME file_name, file_name),
		XMLELEMENT(NAME file_description, file_description),
		XMLELEMENT(NAME external_url, external_url),
		XMLELEMENT(NAME created_time, created_time)
			  )) AS attachments
  FROM attachments where posting_id = """+ str(posting_id[0]) +"""),
		   (SELECT 
    xmlagg(XMLELEMENT(NAME notice_fundings, 
      	XMLELEMENT(NAME funding_agency , funding_agency)
			  )) AS funding_agency
  FROM notice_fundings where posting_id = """+ str(posting_id[0]) +"""),
		   (SELECT 
    xmlagg(XMLELEMENT(NAME award_informations, 
      	XMLELEMENT(NAME bidder_name, bidder_name),
      	XMLELEMENT(NAME address, address), 
      	XMLELEMENT(NAME initial_estimated_value, initial_estimated_value),
		XMLELEMENT(NAME final_estimated_value, final_estimated_value),
		XMLELEMENT(NAME bid_received, bid_recieved),
		XMLELEMENT(NAME contract_duration, contract_duration),
		XMLELEMENT(NAME award_date, award_date)
			  )) AS award_details
  FROM award_details where posting_id = """+ str(posting_id[0]) +""" ),
		   (SELECT 
    xmlagg(XMLELEMENT(NAME notice_cpv_mapping, 
      	XMLELEMENT(NAME notice_id, posting_id),
      	XMLELEMENT(NAME cpv_code, cpv_code),
		XMLELEMENT(NAME is_primary, is_primary)
			  )) AS award_details
  FROM notice_cpv_mapping 
  where posting_id = """+ str(posting_id[0]) +"""),
		   (SELECT 
    xmlagg(XMLELEMENT(NAME notice_cpv_mapping, 
      	XMLELEMENT(NAME notice_id, posting_id),
      	XMLELEMENT(NAME cpv_code, lot_cpv_code), 
      	XMLELEMENT(NAME is_primary, is_primary)
			  )) AS award_details
  FROM  lot_cpv_mapping 
  where posting_id = """+ str(posting_id[0]) +"""),
	 (WITH j AS (select 
        ld.posting_id,
            array_agg(
            json_build_object(

                'title', lot_title, 
                'number', lot_number,
                'actualNumber',lot_actual_number,
                'description',lot_description,
                'grossBudgetEuro',lot_grossbudget,
                'netBudgetEuro', lot_netbudget,
                'grossBudgetLC', lot_grossbudget_lc,
                'netBudgetLC', lot_netbudget_lc,
                'vat',lot_vat,
                'quantity',lot_quantity,
                'minQuantity',lot_min_quantity,
                'maxQuantity',lot_max_quantity,
                'quantityUOM',lot_quantity_uom,
                'contractNumber',contract_number,
                'contractDuration',contract_duration,
                'contractStartDate',contract_start_date,
                'contractEndDate',contract_end_date,
                'lotNuts',lot_nuts,
                'cancellationDate',lot_cancellation_date,
                'lotAwardDate',lot_award_date,
                'isCanceled',lot_is_canceled,
				'contractType',lot_contract_type_actual,
				'lotCPVCodes', lot_cpv_at_source, 
                'awardDetails', case when award_details3 is null then '{}' else award_details3 end,
                'awardCriteria',case when lot_criteria3 is null then '{}' else lot_criteria3 end
            )
            )::text as lot_details3
        from lot_details as ld
        left join (select 
         lot_id, 

                   array_agg(
                json_build_object(
                        'awardWinner',bidder_name,
                        'awardWinnerGroupName',winner_group_name,
                        'grossBudgetEuro',grossawardvalueeuro,
                        'netBudgetEuro',netawardvalueeuro,
                        'grossBudgetLC',grossawardvaluelc,
                        'netBudgetLC',netawardvaluelc,
                        'quantity',award_quantity,
                        'notes',notes
                )	
                )  as award_details3
        from award_details
        where posting_id = """+ str(posting_id[0]) +"""
        group by lot_id) as award_details2
        on award_details2.lot_id = ld.lot_id
	left join (select lot_id,
	array_agg(
	json_build_object(
		
	    'title', lot_criteria_title,
	    'weight',lot_criteria_weight,
	    'isPriceRelated',lot_is_price_related
	   
	    )
	) as lot_criteria3
	from lot_criteria
	where posting_id = """+ str(posting_id[0]) +""" 
	group by lot_id) as lot_criteria2
	on lot_criteria2.lot_id = ld.lot_id
        WHERE ld.posting_id = """+ str(posting_id[0]) +""" 
        group by ld.posting_id)
		
	select XMLELEMENT(NAME lot_details,replace(lot_details3,'\"','')) from j),

	(SELECT 
    	xmlagg(XMLELEMENT(NAME notice_contacts, 
      	XMLELEMENT(NAME org_type, org_type),
		XMLELEMENT(NAME org_name, org_name), 
      	XMLELEMENT(NAME org_description, org_description),
		XMLELEMENT(NAME org_language, org_language),
		XMLELEMENT(NAME org_parent_id,org_parent_id),
		XMLELEMENT(NAME first_name, contact_person),
		XMLELEMENT(NAME address, org_address), 
      	XMLELEMENT(NAME city, org_city),
		XMLELEMENT(NAME state, org_state),
		XMLELEMENT(NAME postal_code, postal_code),
		XMLELEMENT(NAME country, org_country), 
      	XMLELEMENT(NAME phone, org_phone),
		XMLELEMENT(NAME fax, org_fax),
		XMLELEMENT(NAME email, org_email),
		XMLELEMENT(NAME website, org_website)


		)) as notices from customer_details 
		where posting_id= """+ str(posting_id[0]) +""")

		) as Notice from tender 

		where posting_id= """+ str(posting_id[0])
        cursor.execute(sql3)
        results =  cursor.fetchall()
        for result in results:
            output_xml_file.writeNoticeToXMLFile(result[0])
            notice_count += 1
            print(script_name, notice_count)
            if notice_count == 500:
                output_xml_file.copyFinalXMLToServer("xmlfile")
                output_xml_file = gec_common.OutputXML.OutputXML(str(script_name[0]))
                notice_count = 0
	    
    output_xml_file.copyFinalXMLToServer("xmlfile")
