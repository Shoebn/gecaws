import jsons
import web_db_connection
import datetime
import json
from gec_common.cube_class import *
import gec_common.OutputJSON
from datetime import date, datetime, timedelta

# def json_import(json_File):
connection = web_db_connection.get_conn()
cursor = connection.cursor()

today = date.today() 
today_date =  '31 Jan 2024' #end date/to date


yesterday_date = '01 Jan 2024' #start date/from date

#"es_contrat_ca"	1362
#"es_juntadecia"	445
#"pt_base_ca"	13469
#"pt_base_spn"	1142
#

# Fetch the results from the cursor object
script_names = ['es_contrat','es_contrat_ca','es_juntadecia','pt_base_ca','pt_base_spn']

for script_name in script_names:
    notice_count = 0
    output_json_file = gec_common.OutputJSON.OutputJSON(str(script_name))
    sql2 = """select distinct posting_id from tender where is_publish_on_gec is true and (completed_steps != 'Deleted' or completed_steps is null) and date(update_date) between"""
    query2 = sql2 + "'"+ str(yesterday_date) + "'" + " and " + "'" + str(today_date) + "'" + " and script_name = '"  + str(script_name) + "'"
    print(query2)
    cursor.execute(query2)
    posting_ids =  cursor.fetchall()

    for posting_id in posting_ids:
        sql3 = """with object1 as  
	
		(select json_build_object('notice_no',	notice_no,
	            'notice_title',	notice_title,
	            'main_language',	main_language,
	            'est_amount',	est_amount,
	            'currency',	currency,
	            'procurement_method',	procurement_method,
	            'notice_deadline',	to_char(notice_deadline,'YYYY/MM/DD HH24:MI:SS'),
	            'publish_date',	to_char(publish_date,'YYYY/MM/DD HH24:MI:SS'),
	            'script_name',	script_name,
	            'document_fee',	document_fee,
	            'additional_source_id',	additional_source_id,
	            'additional_tender_url',	additional_tender_url,
	            'dispatch_date',  to_char(dispatch_date,'YYYY/MM/DD HH24:MI:SS'),
	            'local_title',	local_title,
                'grossbudgeteuro',	grossbudgeteuro,
                'netbudgeteuro',	netbudgeteuro,
                'grossbudgetlc',	grossbudgetlc,
                'netbudgetlc',	netbudgetlc,
                'vat',	vat,
                'document_type_description',	document_type_description,
                'type_of_procedure',	type_of_procedure,
                'type_of_procedure_actual',	type_of_procedure_actual,
                'notice_summary_english',	notice_summary_english,
                'identifier',	identifier,
                'notice_type',	notice_type,
                'contract_duration',	contract_duration,
                'project_name',	project_name,
                'document_cost',	document_cost,
                'notice_contract_type',	notice_contract_type,
                'source_of_funds',	source_of_funds,
                'class_at_source',	class_at_source,
                'class_codes_at_source',	class_codes_at_source,
                'class_title_at_source',	class_title_at_source,
                'bidding_response_method',	bidding_response_method,
                'notice_text',	notice_text,
                'notice_url',	notice_url,
                'local_description', local_description,
                'tender_quantity',tender_quantity,
                'cpv_at_source',cpv_at_source,
                'tender_id',tender_id,
                'contract_type_actual',contract_type_actual,
                'lot_details',  case when lot_details3 is null then '{}' else lot_details3 end,
                'funding_agencies',case when notice_fundings3 is null then '{}' else notice_fundings3 end,
                'performance_country', case when performance_country3 is null then '{}' else performance_country3 end,
                'performance_state',case when performance_state3 is null then '{}' else performance_state3 end,
                'cpvs', case when notice_cpv_mapping3 is null then '{}' else notice_cpv_mapping3 end,
                'custom_tags', case when custom_tags3 is null then '{}' else custom_tags3 end,
                'customer_details', case when customer_details3 is null then '{}' else customer_details3 end,
                'tender_criteria', case when tender_criteria3 is null then '{}' else tender_criteria3 end,
                'attachments',case when attachments3 is null then '{}' else attachments3 end )
		 ::jsonb as o
 from tender as t
	left join (select ld.posting_id,
		array_agg(json_build_object('lot_title', lot_title,
            'lot_title_english', lot_title_english,
			'lot_number', lot_number,
			'lot_actual_number',lot_actual_number,
			'lot_description',lot_description,
			'lot_description_english',lot_description_english,
			'lot_grossbudget',lot_grossbudget,
			'lot_netbudget', lot_netbudget,
			'lot_grossbudget_lc', lot_netbudget_lc,
			'lot_netbudget_lc', lot_netbudget_lc,
			'lot_vat',lot_vat,
			'lot_quantity',lot_quantity,
			'lot_min_quantity',lot_min_quantity,
			'lot_max_quantity',lot_max_quantity,
			'lot_quantity_uom',lot_quantity_uom,
			'contract_number',contract_number,
			'contract_duration',contract_duration,
			'contract_start_date',to_char(contract_start_date,'YYYY/MM/DD HH24:MI:SS'),
			'contract_end_date',to_char(contract_end_date,'YYYY/MM/DD HH24:MI:SS'),
			'lot_nuts',lot_nuts,
			'lot_cancellation_date',to_char(lot_cancellation_date,'YYYY/MM/DD HH24:MI:SS'),
			'lot_award_date',to_char(lot_award_date,'YYYY/MM/DD HH24:MI:SS'),
			'contract_type',contract_type,
			'lot_is_canceled',lot_is_canceled,
            'lot_class_codes_at_source',lot_class_codes_at_source,
            'lot_cpv_at_source',lot_cpv_at_source,
            'lot_contract_type_actual',lot_contract_type_actual,
			'award_details', case when award_details3 is null then '{}' else award_details3 end,
			'lot_cpvs', case when lot_cpv_mapping3 is null then '{}' else lot_cpv_mapping3 end,
			'lot_criteria',case when lot_criteria3 is null then '{}' else lot_criteria3 end)) as lot_details3
    from lot_details as ld
	left join (select
	 lot_id,
			   array_agg(
			json_build_object(
					'bidder_name',bidder_name,
                    'bidder_country',bidder_country,
					'address',address,
					'initial_estimated_value',initial_estimated_value,
					'final_estimated_value',final_estimated_value,
					'bid_recieved',bid_recieved,
					'contract_duration',contract_duration,
					'award_date',award_date,
					'winner_group_name',winner_group_name,
					'grossawardvalueeuro',grossawardvalueeuro,
					'netawardvalueeuro',netawardvalueeuro,
					'grossawardvaluelc',grossawardvaluelc,
					'netawardvaluelc',netawardvaluelc,
					'award_quantity',award_quantity,
					'notes',notes)
			)  as award_details3
	from award_details
   	where posting_id =  """+ str(posting_id[0])+"""
	group by lot_id) as award_details2
	on award_details2.lot_id = ld.lot_id
				left join (select lot_id,
						   	array_agg(
							json_build_object(
								'lot_cpv_code',lot_cpv_code
								)
							) as lot_cpv_mapping3
			   	from lot_cpv_mapping
			   	where posting_id =  """+ str(posting_id[0])+"""
			  	group by lot_id) as lot_cpv_mapping2
			   	on lot_cpv_mapping2.lot_id = ld.lot_id
			   				left join (select lot_id,
						   	array_agg(
							json_build_object(
									'lot_criteria_title',lot_criteria_title,
									'lot_criteria_weight',lot_criteria_weight,
									'lot_is_price_related',lot_is_price_related
								)
							) as lot_criteria3
							from lot_criteria
							where posting_id =  """+ str(posting_id[0])+"""
							group by lot_id) as lot_criteria2
							on lot_criteria2.lot_id = ld.lot_id
	WHERE ld.posting_id =  """+ str(posting_id[0])+"""
    group by ld.posting_id
 ) lot_details2
 on lot_details2.posting_id = t.posting_id
 	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'funding_agency',funding_agency
			)) as notice_fundings3
		from notice_fundings
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as notice_fundings2
		on notice_fundings2.posting_id = t.posting_id
 	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'performance_country',performance_country
			)) as performance_country3
		from performance_country
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as performance_country2
		on performance_country2.posting_id = t.posting_id
  	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'performance_state',performance_state
			)) as performance_state3
		from performance_state
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as performance_state2
		on performance_state2.posting_id = t.posting_id
	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'cpv_code',cpv_code
			)) as notice_cpv_mapping3
		from notice_cpv_mapping
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as notice_cpv_mapping2
		on notice_cpv_mapping2.posting_id = t.posting_id
	left join (select posting_id,
		array_agg(
		json_build_object(
			'tender_custom_tag_description', tender_custom_tag_description,
			'tender_custom_tag_value',tender_custom_tag_value,
			'tender_custom_tag_company_id',tender_custom_tag_company_id,
			'tender_custom_tag_tender_id',tender_custom_tag_tender_id )) as custom_tags3
		from custom_tags
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as custom_tags2
		on custom_tags2.posting_id = t.posting_id
	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'org_type', org_type,
			'org_name', org_name,
			'org_description', org_description,
			'org_email', org_email,
			'org_address', org_address,
			'org_state', org_state,
			'org_country', org_country,
			'org_language', org_language,
			'org_phone', org_phone,
			'org_fax', org_fax,
			'org_website', org_website,
			'org_parent_id', org_parent_id,
			'org_city', org_city,
			'customer_nuts', customer_nuts,
			'type_of_authority_code',type_of_authority_code,
			'customer_main_activity',customer_main_activity,
			'postal_code',postal_code,
			'contact_person',contact_person
			)) as customer_details3
		from customer_details
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as customer_details2
		on customer_details2.posting_id = t.posting_id
	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'tender_criteria_title',tender_criteria_title,
			'tender_criteria_weight',tender_criteria_weight,
			'tender_is_price_related',tender_is_price_related
			)) as tender_criteria3
		from tender_criteria
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as tender_criteria2
		on tender_criteria2.posting_id = t.posting_id
	left join (select
	posting_id,
		array_agg(
		json_build_object(
			'file_type',file_type,
			'file_name',file_name,
			'file_description',file_description,
			'external_url',external_url,
			'file_size',file_size
			)) as attachments3
		from attachments
		WHERE posting_id =  """+ str(posting_id[0])+"""
		group by posting_id) as attachments2 on attachments2.posting_id = t.posting_id WHERE t.posting_id =  """+ str(posting_id[0])+""")
	select o
		|| (select * from( select json_build_object(
		 
		'eligibility',	eligibility,
		'crawled_at',	crawled_at,
		'related_tender_id',	related_tender_id,
		'additional_source_name',	additional_source_name,
		'earnest_money_deposit',	earnest_money_deposit,
		'document_purchase_start_time',	document_purchase_start_time,
		'document_purchase_end_time',	document_purchase_end_time,
		'pre_bid_meeting_date',	pre_bid_meeting_date,
		'document_opening_time',	document_opening_time,
        'tender_min_quantity',tender_min_quantity,
        'tender_max_quantity',tender_max_quantity,
        'tender_quantity_uom',tender_quantity_uom,
        'tender_contract_number',tender_contract_number,
        'tender_contract_start_date',to_char(tender_contract_start_date,'YYYY/MM/DD HH24:MI:SS'),
		'tender_contract_end_date',to_char(tender_contract_end_date,'YYYY/MM/DD HH24:MI:SS'),
        'tender_is_canceled',tender_is_canceled,
        'tender_cancellation_date',to_char(tender_cancellation_date,'YYYY/MM/DD HH24:MI:SS'),
        'tender_award_date',to_char(tender_award_date,'YYYY/MM/DD HH24:MI:SS'),
        'completed_steps',completed_steps,
        'is_publish_assumed',is_publish_assumed,
        'is_deadline_assumed',is_deadline_assumed,
		'category',	category)::jsonb as o  from tender as t2
		WHERE t2.posting_id =  """+ str(posting_id[0])+""") as object2)   from  object1"""
        cursor.execute(sql3)
        results =  cursor.fetchall()
        for result in results:
            output_json_file.writeNoticeToJSONFile(jsons.dump(result[0]))
            notice_count += 1  
            if notice_count == 500:
                output_json_file.copyFinalJSONToServer("Sample_output")
                output_json_file = gec_common.OutputJSON.OutputJSON(str(script_name))
                notice_count = 0
    output_json_file.copyFinalJSONToServer("Sample_output")
