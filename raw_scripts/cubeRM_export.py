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


sql = "select distinct script_name from tender where update_date between "
query = sql + "'" + str(yesterday_date[0][0]) + "'" + " and " + "'" +  str(today_date) + "'"
cursor.execute(query)


# Fetch the results from the cursor object
script_names = cursor.fetchall()

for script_name in script_names:
    output_json_file = gec_common.OutputJSON.OutputJSON(str(script_name[0]))
    sql2 = """select distinct posting_id from tender where customer_details ->> 'org_name' 
    is not null and notice_title is not null and local_title is not null and publish_date is not null and update_date between"""
    query2 = sql2 + "'"+ str(yesterday_date[0][0]) + "'" + " and " + "'" + str(today_date) + "'" + " and script_name = '"  + str(script_name[0]) + "'"
    cursor.execute(query2)
    posting_ids =  cursor.fetchall()
    cubeRM_export_log_query = "INSERT INTO cubeRM_export_log (posting_ids,created_time) VALUES ('"+str(posting_ids)+"','"+str(today_date)+"')"
    cursor.execute(cubeRM_export_log_query)
    connection.commit()
    for posting_id in posting_ids:
        sql3 = """select crawled_at,script_name,notice_no,related_tender_id,
        additional_source_name,additional_source_id,dispatch_date,publish_date,
        notice_deadline,notice_type,document_type_description ,type_of_procedure,
        type_of_procedure_actual,notice_title,local_title,notice_summary_english,
        grossbudgeteuro,netbudgeteuro,grossbudgetlc,netbudgetlc,vat,notice_url,
        additional_tender_url,currency,
        main_language,identifier,notice_text,local_description from tender where posting_id ="""
        query3 = sql3 + str(posting_id[0])
        cursor.execute(query3)
        results =  cursor.fetchall()
        
        for result in results:
            tender_data = tender()
            tender_data.crawledAt  = result[0]
            tender_data.sourceName  = result[1]
            if tender_data.tenderId != None and tender_data.tenderId != '':
                tender_data.tenderId  = str(result[1])+str('_')+str(result[2])+str('_')+str(posting_id[0])
            else:
                tender_data.tenderId  = str(result[1])+str('_')+str(posting_id[0])
            tender_data.relatedTenderId  = result[3]
            tender_data.additionalSourceName  = result[4]
            tender_data.additionalSourceId  = result[5]
            tender_data.dispatchDate  = result[6]
            tender_data.publicationDate  = result[7]
            tender_data.submissionDeadline  = result[8]
            documentType  = result[9]
            if documentType == 2 or documentType ==3:
                tender_data.documentType = 1
            elif documentType == 4 or documentType == 5 or documentType == 6 or documentType ==8:
                tender_data.documentType = 2
            elif documentType == 7:
                tender_data.documentType = 3
            elif documentType == 16:
                tender_data.documentType = 4
            else:
                tender_data.documentType = 0
            tender_data.documentTypeDescription  = result[10]
            tender_data.typeOfProcedure  = result[11]
            tender_data.typeOfProcedureActual  = result[12]
            tender_data.title  = result[13]
            tender_data.localTitle  = result[14]
            tender_data.description  = result[15]
            tender_data.grossBudgetEuro  = result[16]
            tender_data.netBudgetEuro  = result[17]
            tender_data.grossBudgetLC  = result[18]
            tender_data.netBudgetLC  = result[19]
            tender_data.vat  = result[20]
            tender_data.tenderURL  = result[21]
            tender_data.additionalTenderURL  = result[22]
            tender_data.currency  = result[23]
            tender_data.language  = result[24]
            tender_data.identifier  = str(posting_id[0])
            tender_data.htmlBody += result[26]
            tender_data.localDescription = result[27]
            
            sql12 = "select performance_country from performance_country where posting_id = "
            query12 = sql12  + str(posting_id[0])
            cursor.execute(query12)
            results_country =  cursor.fetchall()
            country = ''
            for result_country in results_country:
                country += str(result_country[0])
                country += ','
            tender_data.country = country.rstrip(',')
            
            sql13 = "select cpv_code from notice_cpv_mapping where posting_id = "
            query13 = sql13  + str(posting_id[0])
            cursor.execute(query13)
            results_tenderCPVCode =  cursor.fetchall()
            tender_data_tenderCPVCode = ''
            for result_tenderCPVCode in results_tenderCPVCode:
                tenderCPVCode  = result_tenderCPVCode[0]
                tender_data_tenderCPVCode += str(tenderCPVCode)
                tender_data_tenderCPVCode += ','
            tender_data.tenderCPVCodes = tender_data_tenderCPVCode.rstrip(',')
                

            sql4 = """select org_name,org_country,org_city,org_address,postal_code,org_email,org_phone,
                    customer_nuts,type_of_authority_code,customer_main_activity,contact_person 
                    from customer_details where posting_id = """
            query4 = sql4  + str(posting_id[0])
            cursor.execute(query4)
            results_customer =  cursor.fetchall()
            for result_customer in results_customer:
                customer_data = customer()
                customer_data.name  = result_customer[0]
                customer_data.country  = result_customer[1]
                customer_data.city  = result_customer[2]
                customer_data.street  = str(result_customer[10]) + ' ' +str(result_customer[3])
                if 'None' in customer_data.street:
                    customer_data.street = customer_data.street.replace('None','').strip()
                customer_data.postalCode  = result_customer[4]
                customer_data.email  = result_customer[5]
                customer_data.phone  = result_customer[6]
                customer_data.nuts  = result_customer[7]
                customer_data.typeOfAuthorityCode  = result_customer[8]
                customer_data.mainActivity  = result_customer[9]
                tender_data.customer.append(customer_data)
                
            sql5 = """select file_description,external_url,file_size
                    from attachments where external_url is not null and  file_description is not null and posting_id = """
            query5 = sql5  + str(posting_id[0])
            cursor.execute(query5)
            results_attachments =  cursor.fetchall()
            for result_attachments in results_attachments:
                attachments_data = attachments()
                attachments_data.description  = result_attachments[0]
                attachments_data.url  = result_attachments[1]
                attachments_data.size  = result_attachments[2]
                attachments_data.attachments_cleanup()
                tender_data.attachments.append(attachments_data)
                
            sql6 = """select tender_custom_tag_description,tender_custom_tag_value,tender_custom_tag_company_id
                    from custom_tags where posting_id = """
            query6 = sql6  + str(posting_id[0])
            cursor.execute(query6)
            results_customTags =  cursor.fetchall()
            for result_customTags in results_customTags:
                customTags_data = customTags()
                customTags_data.description  = result_customTags[0]
                customTags_data.value  = result_customTags[1]
                customTags_data.companyId  = result_customTags[2]
                tender_data.customTags.append(customTags_data)
                
            sql7 = """select tender_criteria_title,tender_criteria_weight,tender_is_price_related
                    from tender_criteria where posting_id = """
            query7 = sql7  + str(posting_id[0])
            cursor.execute(query7)
            results_awardCriteria =  cursor.fetchall()
            for result_awardCriteria in results_awardCriteria:
                awardCriteria_data = awardCriteria()
                awardCriteria_data.title  = result_awardCriteria[0]
                awardCriteria_data.weight  = result_awardCriteria[1]
                awardCriteria_data.isPriceRelated  = result_awardCriteria[2]
                awardCriteria_data.awardCriteria_cleanup()
                tender_data.awardCriteria.append(awardCriteria_data)
                
            sql11 = "select distinct lot_id  from lot_details where posting_id = "
            query11 = sql11  + str(posting_id[0])
            cursor.execute(query11)
            lot_ids =  cursor.fetchall()
            for lot_id in lot_ids:
                
                sql8 = """select lot_number,lot_title,lot_description,lot_grossbudget,lot_netbudget,
                    lot_grossbudget_lc,lot_netbudget_lc,lot_vat,lot_quantity,lot_min_quantity,
                    lot_max_quantity,lot_quantity_uom,contract_number,contract_duration,contract_start_date,contract_end_date,
                    lot_nuts,lot_is_canceled,lot_cancellation_date,lot_award_date,contract_type,lot_actual_number
                    from lot_details where lot_id = """
                query8 = sql8  + str(lot_id[0])
                cursor.execute(query8)
                results_lots =  cursor.fetchall()
                for result_lots in results_lots:
                    lots_data = lots()
                    lots_data.number  = result_lots[0]
                    lots_data.title  = result_lots[1]
                    lots_data.description  = result_lots[2]
                    lots_data.grossBudgetEuro  = result_lots[3]
                    lots_data.netBudgetEuro  = result_lots[4]
                    lots_data.grossBudgetLC  = result_lots[5]
                    lots_data.netBudgetLC  = result_lots[6]
                    lots_data.vat  = result_lots[7]
                    lots_data.quantity  = result_lots[8]
                    lots_data.minQuantity  = result_lots[9]
                    lots_data.maxQuantity  = result_lots[10]
                    lots_data.quantityUOM  = result_lots[11]
                    lots_data.contractNumber  = result_lots[12]
                    lots_data.contractDuration  = result_lots[13]
                    lots_data.contractStartDate  = result_lots[14]
                    lots_data.contractEndDate  = result_lots[15]
                    lots_data.lotNuts  = result_lots[16]
                    lots_data.isCanceled  = result_lots[17]
                    lots_data.cancellationDate  = result_lots[18]
                    lots_data.lotAwardDate  = result_lots[19]
                    lots_data.contractType  = result_lots[20]
                    lots_data.actualNumber  = result_lots[21]
                    
                
                    sql9 = """select bidder_name,winner_group_name,grossawardvalueeuro,
                    netawardvalueeuro,grossawardvaluelc,netawardvaluelc,award_quantity,notes
                    from award_details where lot_id = """
                    query9 = sql9  + str(lot_id[0])
                    cursor.execute(query9)
                    results_awardDetails =  cursor.fetchall()
                    for result_awardDetails in results_awardDetails:
                        awardDetails_data = awardDetails()
                        awardDetails_data.awardWinner  = result_awardDetails[0]
                        awardDetails_data.awardWinnerGroupName  = result_awardDetails[1]
                        awardDetails_data.grossBudgetEuro  = result_awardDetails[2]
                        awardDetails_data.netBudgetEuro  = result_awardDetails[3]
                        awardDetails_data.grossBudgetLC  = result_awardDetails[4]
                        awardDetails_data.netBudgetLC  = result_awardDetails[5]
                        awardDetails_data.quantity  = result_awardDetails[6]
                        awardDetails_data.notes  = result_awardDetails[7]
                        awardDetails_data.awardDetails_cleanup()
                        lots_data.awardDetails.append(awardDetails_data)
                            
                    sql10 = """select lot_criteria_title,lot_criteria_weight,lot_is_price_related
                    from lot_criteria where lot_id = """
                    query10 = sql10  + str(lot_id[0])
                    cursor.execute(query10)
                    results_awardCriteria =  cursor.fetchall()
                    for result_awardCriteria in results_awardCriteria:
                        awardCriteria_data = awardCriteria()
                        awardCriteria_data.title  = result_awardCriteria[0]
                        awardCriteria_data.weight  = result_awardCriteria[1]
                        awardCriteria_data.isPriceRelated  = result_awardCriteria[2]    
                        awardCriteria_data.awardCriteria_cleanup()
                        lots_data.awardCriteria.append(awardCriteria_data)
                        
                    sql14 = "select lot_cpv_code from lot_cpv_mapping where lot_id = "
                    query14 = sql14  + str(lot_id[0])
                    cursor.execute(query14)
                    results_lotCPVCodes =  cursor.fetchall()
                    tender_data_tenderCPVCode = ''
                    for result_lotCPVCodes in results_lotCPVCodes:
                        tenderCPVCode  = result_lotCPVCodes[0]
                        tender_data_tenderCPVCode += str(tenderCPVCode)
                        tender_data_tenderCPVCode += ','
                    lots_data.lotCPVCodes = tender_data_tenderCPVCode.rstrip(',')
                lots_data.lots_cleanup()
                tender_data.lots.append(lots_data)
                
            tender_data.tender_cleanup()
            output_json_file.writeNoticeToJSONFile(jsons.dump(tender_data))
            
    output_json_file.copyFinalJSONToServer("cubeRM_output")
