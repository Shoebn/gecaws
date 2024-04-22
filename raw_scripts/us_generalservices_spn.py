# script_name:'us_generalservices_spn'

# urls:"https://www.generalservices.state.nm.us/state-purchasing/active-itbs-and-rfps/active-procurements/"

# page_no://*[@id="ctl00_ContentPlaceHolder1_rgProcurements_ctl00"]/tbody/tr			tender_html_element			3

# performance_country:'US'

# currancy:'USD'

# main_language:'EN'   

# procurement_method:2

# notice_type:4

# publish_date:'threshold'

# 			*************************************************************************************************************
# document_type_description:Type		tender_html_element
# notice_deadline:Due Date			tender_html_element
# notice_no:ProcurementID				tender_html_element
# local_title:Title					tender_html_element
# notice_url:ProcurementID			tender_html_element
# notice_text:page_main			Note:Take "tender_html_element" data also.

# 			*************************************************************************************************************
# ref_notice_no:"40-80500-23-17072"
# notice_summary_english:Procurement Details >> Commodity Description			page_main
# local_description:Procurement Details >> Commodity Description				page_main
			
# ref_notice_no:"40-U6900-24-CP006"
# est_amount:Procurement Details >> Amount										page_main
# grossbudgetlc:Procurement Details >> Amount									page_main
# tender_contract_start_date:Procurement Details >> Start						page_main
# tender_contract_end_date:Procurement Details >> End							page_main
# contract_duration:Procurement Details >> Quantity of the service				page_main

			
# 			*************************************************************************************************************

# customer_detail[]
#     org_country:'US'
#     org_language:'EN'
#     org_name:Agency Name		tender_html_element
# 		cmt:split org_name.Here "80500 - NM DEPARTMENT OF TRANSPORTATION" grab only "NM DEPARTMENT OF TRANSPORTATION" in org_name.
	
# 	ref_notice_no:"40-80500-23-17072"
# 	contact_person:Procurement Details >> Buyer						page_main
# 			cmt:If blank then use below field.
	
# 	ref_notice_no:"40-U6900-24-CP006"
# 	contact_person:Procurement Details >> Contractor's Name			page_main
	
#   org_address:Procurement Details >> Address						page_main
# 	org_city:Procurement Details >> City							page_main
# 	org_state:Procurement Details >> State/Province					page_main
# 	postal_code:Procurement Details >> Zip							page_main
	
	
# 			*************************************************************************************************************
# attachments_details[]
# 	file_name:Tender Documents
# 	external_url:Files >> Download all as .zip file					page_main
# 	file_type:Files >> Download all as .zip file					page_main
# 		cmt:split file_type from external_url.
