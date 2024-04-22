use VPN:USA	or USA,Nebraska


	**************************************************************us_nebraska_spn****************************************************
In "us_nebraska_spn" grab the data from the table after keyword "Current Bid Opportunities" and "In Process of Being Awarded".

script_name:'us_nebraska_spn'

urls:"https://das.nebraska.gov/materiel/bidopps.html"

page_no:/html/body/div[3]/table[1]/tbody/tr			tender_html_element		    3	
		/html/body/div[3]/table[2]/tbody/tr


performance_country:'US'

currancy:'USD'

main_language:'EN'   

procurement_method:2

notice_type:4


				*************************************************************************************
local_title:DESCRIPTION                             tender_html_element
class_codes_at_source:CATEGORY -NIGP CODE           tender_html_element
				cmt:grab the number after "-".
class_title_at_source:CATEGORY -NIGP CODE           tender_html_element
				cmt:grab the text before "-".
notice_deadline:OPENING DATE                        tender_html_element
document_opening_time:OPENING DATE                  tender_html_element
document_type_description:TYPE                      tender_html_element
notice_no:SOLICITATION NUMBER                       tender_html_element
        cmt:if not availabel then split from notice_url.
publish_date:LAST UPDATED                           tender_html_element


notice_summary_english:PROJECT DESCRIPTION          page_details
                cmt:split between "PROJECT DESCRIPTION" and "Written Questions".
local_description:PROJECT DESCRIPTION               page_details
                cmt:split between "PROJECT DESCRIPTION" and "Written Questions".




customer_details[]
    org_country:'US'
    org_language:'EN'
    contact_person:BUYER(S)         tender_html_element
    org_name:AGENCY                 tender_html_element
    
    org_phone:Phone:                page_details
    org_email:Email:                page_details
    
    
attachments_details[]               page_details
        ref_url:"https://das.nebraska.gov/materiel/purchasing/6861%20OF/6861%20OF.html"
            
            
            file_name:PROJECT DOCUMENTS
                    cmt:if external_url was not there then don't grab file_name.
            external_url:DOCUMENT FORMAT(S)
            file_type:DOCUMENT FORMAT(S)
                    cmt:grab only file_extension.
                    
                    
                    
                    
                    
                    
	**************************************************************us_nebraska_ca****************************************************
In "us_nebraska_spn" grab the data from the table after keyword "Awarded Bids".

script_name:'us_nebraska_ca'

urls:"https://das.nebraska.gov/materiel/bidopps.html"

page_no:/html/body/div[3]/table[3]/tbody/tr			tender_html_element		    3	
		
performance_country:'US'

currancy:'USD'

main_language:'EN'   

procurement_method:2

notice_type:7


				*************************************************************************************
local_title:DESCRIPTION                             tender_html_element
class_codes_at_source:CATEGORY -NIGP CODE           tender_html_element
				cmt:grab the number after "-".
class_title_at_source:CATEGORY -NIGP CODE           tender_html_element
				cmt:grab the text before "-".
document_opening_time:OPENING DATE                  tender_html_element
related_tender_id:SOLICITATION NUMBER               tender_html_element
publish_date:LAST UPDATED                           tender_html_element



notice_summary_english:PROJECT DESCRIPTION          page_details
                cmt:split between "PROJECT DESCRIPTION" and "Written Questions".
local_description:PROJECT DESCRIPTION               page_details
                cmt:split between "PROJECT DESCRIPTION" and "Written Questions".


customer_details[]
    org_country:'US'
    org_language:'EN'
    contact_person:BUYER(S)         tender_html_element
    org_name:AGENCY                 tender_html_element
    
    org_phone:Phone:                page_details
    org_email:Email:                page_details
    
    
attachments_details[]               page_details
        ref_url:"https://das.nebraska.gov/materiel/purchasing/6677/6677.html"
            file_name:PROJECT DOCUMENTS
                    cmt:if external_url was not there then don't grab file_name.
            external_url:DOCUMENT FORMAT(S)
            file_type:DOCUMENT FORMAT(S)
                    cmt:grab only file_extension.
                    


lot_details[]
    lot_title:DESCRIPTION                             tender_html_element
        
        award_details[]
            award_date:LETTER OF INTENT TO AWARD ISSUED >> DATE	        tender_html_element
            bidder_name:LETTER OF INTENT TO AWARD ISSUED >> VENDOR(S)   tender_html_element



