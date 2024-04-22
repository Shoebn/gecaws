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
today_date = datetime.now()

query_yesterday = "select TO_CHAR(max(created_time),'YYYY-MM-DD HH24:MI:SS.FF6') from cubeRM_export_log"
cursor.execute(query_yesterday)
yesterday_date = cursor.fetchall()


sql = """select distinct script_name from tender where (script_name ilike 'it_%' or script_name ilike 'fr_%' or script_name ilike 'br_%'  or 
script_name ilike 'sa_%' or script_name ilike 'cn_%' or script_name ilike 'se_%' or script_name ilike 'no_%' or script_name ilike 'th_gprogo%' 
or script_name ilike 'ac_ungm%' or script_name ilike 'gb_findtenserv%'  or script_name ilike 'pt_base%' or script_name ilike 'pl_logintrade%'
or script_name ilike 'pl_propublico%' or script_name ilike 'pl_platformza_spn%' or script_name ilike 'ar_comprar%' or script_name ilike 'nl_tenderned_spn%'
or script_name = 'pl_smartpzp_spn' or script_name = 'pl_platformaeb_spn' or script_name = 'pl_platformaeb_ca' or script_name = 'nl_tenderned_ca' 
or script_name = 'nl_tenderned_pp'or  script_name = 'nl_tenderned_ca' or script_name = 'ca_merx_spn' or 
script_name = 'ro_elicitatie_spn' or 
script_name = 'ro_elicitatie_ca' or 
script_name = 'ca_merx_ca' or
script_name ilike 'au_tenders%' or 
script_name ilike 'za_etenders%' or
script_name = 'iq_businews_spn' or 
script_name ilike 'ph_philgeps%' or 
script_name = 'sg_singhealth_spn' or 
script_name = 'ae_proc_spn' or 
script_name = 'be_enabel_spn' or 
script_name ilike 'ar_bcra_%' or 
script_name = 'vn_muasamcongopp_pp' or 
script_name = 'vn_muasamcong_pp' or
script_name = 'ar_santacruz_spn' or 
script_name = 'au_sa_ca' or
script_name = 'ca_bcbid_ca' or 
script_name = 'in_gem_spn' or
script_name = 'in_cpppcn_ca' or 
script_name = 'sg_sesami_spn' or
script_name = 'sg_sesaminet_spn' or  
script_name = 'au_vic_spn' or
script_name = 'au_nsw_spn' or
script_name = 'vn_muasamcong_ca' or
script_name = 'nl_s2cmercell_spn' or 
script_name = 'ar_bcra_ca' or
script_name = 'ar_santafe_spn' or
script_name = 'in_cpppcn_spn' or
script_name = 'in_gem_ca' or
script_name ilike 'in_mahatenders%' or
script_name ilike 'in_mptenders%' or
script_name ilike 'in_odisha%' or
script_name ilike 'in_wbtenders%' or
script_name = 'ph_philgeps_ca' or
script_name = 'ar_bcra_ca' or
script_name = 'au_nsw_pp' or
script_name = 'za_ecdpw_ca' or
script_name = 'au_sa_spn' or
script_name = 'au_vic_ca' or
script_name = 'ca_bcbid_spn' or
script_name = 'au_vendorpanel_spn' or
script_name = 'au_wa_ca' or
script_name = 'au_wa_spn' or
script_name = 'ae_esupply_spn' or
script_name = 'iq_petrochina_spn' or
script_name = 'ae_mof_spn' or
script_name = 'za_ecdpw_spn' or
script_name = 'nl_negometrix_spn' or
script_name = 'ph_philgeps_ca' or
script_name = 'ca_bidsandten_spn' or
script_name = 'mx_chihua_spn' or
script_name = 'za_satender_spn' or
script_name = 'ru_zakupki_spn' or
script_name = 'tr_ilan_spn' or
script_name = 'mfa_nato_spn' or
script_name = 'ca_buyandsell_spn' or
script_name = 'se_kommersannons_ca' or
script_name = 'se_kommersannons_pp' or
script_name = 'be_publicproc_ca'
) and update_date between """
query = sql + "'" + str(yesterday_date[0][0]) + "'" + " and " + "'" +  str(today_date) + "'"
cursor.execute(query)


# Fetch the results from the cursor object
script_names = cursor.fetchall()

for script_name in script_names:
    notice_count = 0
    output_json_file = gec_common.OutputJSON.OutputJSON(str(script_name[0]))
    sql2 = """select distinct posting_id from tender where is_publish_on_gec is true and (completed_steps != 'Deleted' or completed_steps is null) and update_date between"""
    query2 = sql2 + "'"+ str(yesterday_date[0][0]) + "'" + " and " + "'" + str(today_date) + "'" + " and script_name = '"  + str(script_name[0]) + "'"
    cursor.execute(query2)
    posting_ids =  cursor.fetchall()
    cubeRM_export_log_query = "INSERT INTO cubeRM_export_log (posting_ids,created_time) VALUES ('"+str(posting_ids)+"','"+str(today_date)+"')"
    cursor.execute(cubeRM_export_log_query)
    connection.commit()
    for posting_id in posting_ids:
        sql3 = """with object1 as  (
	
	
		(select json_build_object(
        'tenderId',	case when notice_no is not null and notice_no != '' then notice_no else  script_name  || '_' || t.posting_id::text end ,
        'title',	notice_title,
        'language',	main_language,
        'currency',	currency,
        'submissionDeadline',	to_char(case when is_deadline_assumed = true then null else notice_deadline end ,'YYYY/MM/DD HH24:MI:SS'),
        'publicationDate',	to_char(publish_date,'YYYY/MM/DD HH24:MI:SS'),
        'sourceName',	script_name,
        'crawledAt',	crawled_at,
        'relatedTenderId',	related_tender_id,
        'additionalSourceName',	additional_source_name,
        'additionalSourceId',	additional_source_id,
        'additionalTenderURL',	additional_tender_url,
        'dispatchDate',	dispatch_date,
        'localTitle',	local_title,
        'grossBudgetEuro',	grossbudgeteuro,
        'netBudgetEuro',	netbudgeteuro,
        'grossBudgetLC',	grossbudgetlc,
        'netBudgetLC',	netbudgetlc,
        'vat',	vat,
        'documentTypeDescription',	document_type_description,
        'typeOfProcedure',	type_of_procedure,
        'typeOfProcedureActual',	type_of_procedure_actual,
        'description',	notice_summary_english,
        'identifier',	t.posting_id::text,
        'documentType',	case when notice_type = 2 or notice_type = 3 then 1 
        when notice_type = 4 or notice_type = 5 or notice_type = 6 or notice_type = 8 then 2
        when notice_type = 7  then 3
        when notice_type = 16  then 4 else 0 end,
        'htmlBody',	notice_text,
        'tenderURL',	notice_url,
	'contractType', contract_type_actual,
        'localDescription', local_description,
        'lots', case when script_name ilike 'br_conlicitacao%'  then null when is_lot_default = true then null else lot_details3 end,
		'tenderCPVCodes', cpv_at_source,	
        'country', case when performance_country2.performance_country is null then '{}' else performance_country2.performance_country end,
        'customTags', case when custom_tags3 is null then '{}' else custom_tags3 end,
        'customer', case when customer_details3 is null then '{}' else customer_details3 end,
        'awardCriteria', case when tender_criteria3 is null then '{}' else tender_criteria3 end,
        'attachments',case when attachments3 is null then '{}' else attachments3 end
        )::jsonb as o
     from tender as t
        left join (select 
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
            ) as lot_details3
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
        where posting_id =  """+ str(posting_id[0])+"""
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
            performance_country


            from performance_country
            WHERE posting_id =  """+ str(posting_id[0])+"""
            ) as performance_country2
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
                'description', tender_custom_tag_description,
                'value',tender_custom_tag_value,
                'companyId',tender_custom_tag_company_id
                )) as custom_tags3
            from custom_tags
            WHERE posting_id =  """+ str(posting_id[0])+"""
            group by posting_id) as custom_tags2
            on custom_tags2.posting_id = t.posting_id

        left join (select 
        posting_id,
            array_agg(
            json_build_object( 
                'name', org_name,
                'email', org_email,
                'street', org_address,
                'country', org_country,
                'phone', org_phone,
                'city', org_city,
                'nuts', customer_nuts,
                'typeOfAuthorityCode',type_of_authority_code,
                'mainActivity',customer_main_activity,
                'postalCode',postal_code
                )) as customer_details3
            from customer_details
            WHERE posting_id =  """+ str(posting_id[0])+"""
            group by posting_id) as customer_details2
            on customer_details2.posting_id = t.posting_id

        left join (select 
        posting_id,
            array_agg(
            json_build_object( 
                'title', tender_criteria_title,
                'weight',tender_criteria_weight,
                'isPriceRelated',tender_is_price_related
                )) as tender_criteria3
            from tender_criteria
            WHERE posting_id =  """+ str(posting_id[0])+"""
            group by posting_id) as tender_criteria2
            on tender_criteria2.posting_id = t.posting_id

        left join (select 
        posting_id,
            array_agg(
            json_build_object( 
                'description',file_description,
                'url',external_url,
                'size',file_size
                )) as attachments3
            from attachments
            WHERE posting_id =  """+ str(posting_id[0])+"""
            group by posting_id) as attachments2
            on attachments2.posting_id = t.posting_id
         WHERE t.posting_id =  """+ str(posting_id[0])+""") 
		
		
		)
		 



select case when (o ->> 'lots') is not null then o else o || (select * from( select json_build_object(
		 
		'quantity', CASE 
        	WHEN tender_quantity ~ '\d+' THEN CAST(regexp_replace(tender_quantity, '\D', '', 'g') AS INTEGER) 
        	ELSE NULL 
		END,
		'minQuantity',	tender_min_quantity,
		'maxQuantity', tender_max_quantity,
		'quantityUOM',	tender_quantity_uom,
		'contractNumber',	tender_contract_number,
		'contractDuration', contract_duration,
		'contractStartDate', tender_contract_start_date,
		'contractEndDate', tender_contract_end_date,
		'isCanceled', tender_is_canceled,
		'cancellationDate',	tender_cancellation_date,
		'lotAwardDate',	tender_award_date,
'awardDetails',  case when (select 
          

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
        where posting_id = """+ str(posting_id[0])+"""
        ) is not null then  (select 
          

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
        where posting_id = """+ str(posting_id[0])+"""
        )  else '{}' end )::jsonb as o  from tender as t2
		WHERE t2.posting_id =  """+ str(posting_id[0])+""") as object2) end as o   from  object1"""
        cursor.execute(sql3)
        results =  cursor.fetchall()
        for result in results:
            output_json_file.writeNoticeToJSONFile(jsons.dump(result[0]))
            notice_count += 1  
            if notice_count == 500:
                output_json_file.copyFinalJSONToServer("cubeRM_output")
                output_json_file = gec_common.OutputJSON.OutputJSON(str(script_name[0]))
                notice_count = 0
    output_json_file.copyFinalJSONToServer("cubeRM_output")
