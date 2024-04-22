# script_name:'us_njstart_spn'

# urls:"https://www.njstart.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"

# page_no:tender_html_element 	//*[@id="bidSearchResultsForm:bidResultId_data"]/tr 	10     

# performance_country:'US'

# currancy:'USD'	

# main_language:'EN'      

# procurement_method:2

# notice_type:4

# notice_no : tender_html_element > Bid Solicitation #              Note:If notice_no is not available then grab from notice_url

# local_title : tender_html_element > Description

# notice_deadline : tender_html_element > Bid Opening Date         Note:Grab time also

# notice_url : tander_html_element > Bid Solicitation #

# notice_text: page_detail 		Note:Take "tender_html_element" data also

# publish_date : page_detail > Available Date           Note:Grab time also

# document_opening_time : page_detail > 	Bid Opening Date

# document_purchase_start_time: page_detail > Blanket/Contract

# document_purchase_end_time : page_detail > Blanket/Contract End Date

# document_type_description : page_detail > Retainage

# pre_bid_meeting_date: page_detail > Pre Bid Conference

# customer_detail[] > page_detail
#     org_name: page_detail > Organization
#     contact_person : tender_html_element > Buyer
#     org_address : page_detail > Location , Department
#     org_phone: page_detail  > Info Contact      Note:present than take          
#     org_email: page_detail > Info Contact      Note:present than take           
#     org_country : 'US'
#     org_currency : 'USD'
#     org_language : 'EN'

# attachments[]  : page_detail > File Attachments
#     file_name  : page_detail > File Attachments      Note:Don't take file extention
#     file_type  : page_detail > File Attachments      Note:Take only file extention
#     external_url  :  page_detail > File Attachments

# lot_detail[]  : page_detail > Item Information
#     lot_title : page_detail > NIGP Code     Note:Splite after numeric value..........Don't take numeric value
#     lot_quantity :  page_detail > Qty

#*******************************************************************************************************************************************************

# script_name:'us_arkansas_spn'

# urls:"https://arbuy.arkansas.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"

# page_no:tender_html_element 	//*[@id="bidSearchResultsForm:bidResultId_data"]/tr 	10     

# performance_country:'US'

# currancy:'USD'	

# main_language:'EN'      

# procurement_method:2

# notice_type:4

# notice_no : tender_html_element > Bid Solicitation #             Note:If notice_no is not available then grab from notice_url

# local_title : tender_html_element > Description

# notice_deadline : tender_html_element > Bid Opening Date         Note:Grab time also

# notice_url : tander_html_element > Bid Solicitation #

# notice_text: page_detail 		Note:Take "tender_html_element" data also

# publish_date : page_detail > Available Date           Note:Grab time also

# document_opening_time : page_detail > 	Bid Opening Date

# document_type_description : page_detail > Retainage

# pre_bid_meeting_date: page_detail > Pre Bid Conference

# customer_detail[] > page_detail
#     org_name: page_detail > Organization
#     contact_person : tender_html_element > Buyer
#     org_address : page_detail > Location , Department
#     org_phone: page_detail  > Info Contact      Note:present than take          
#     org_email: page_detail > Info Contact      Note:present than take           
#     org_country : 'US'
#     org_currency : 'USD'
#     org_language : 'EN'

# attachments[]  : page_detail > File Attachments
#     file_name  : page_detail > File Attachments      Note:Don't take file extention
#     file_type  : page_detail > File Attachments      Note:Take only file extention
#     external_url  :  page_detail > File Attachments

# lot_detail[]  : page_detail > Item Information
#     lot_title : page_detail > NIGP Code     Note:Splite after numeric value..........Don't take numeric value
#     lot_quantity :  page_detail > Qty



#*******************************************************************************************************************************************************

# script_name:'us_bidbuy_spn'

# urls:"https://www.bidbuy.illinois.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"

# page_no:tender_html_element 	//*[@id="bidSearchResultsForm:bidResultId_data"]/tr 	10     

# performance_country:'US'

# currancy:'USD'	

# main_language:'EN'      

# procurement_method:2

# notice_type:4

# notice_no : tender_html_element > Bid Solicitation #              Note:If notice_no is not available then grab from notice_url

# local_title : tender_html_element > Description

# notice_deadline : tender_html_element > Bid Opening Date         Note:Grab time also

# notice_url : tander_html_element > Bid Solicitation #

# notice_text: page_detail 		Note:Take "tender_html_element" data also

# publish_date : page_detail > Available Date           Note:Grab time also

# document_opening_time : page_detail > 	Bid Opening Date

# document_type_description : page_detail > Retainage

# pre_bid_meeting_date: page_detail > Pre Bid Conference

# customer_detail[] > page_detail
#     org_name: page_detail > Organization
#     contact_person : tender_html_element > Buyer
#     org_address : page_detail > Location , Department
#     org_phone: page_detail  > Info Contact      Note:present than take          
#     org_email: page_detail > Info Contact      Note:present than take           Ref_uel="https://www.bidbuy.illinois.gov/bso/external/bidDetail.sdo?docId=24-557THA-ENGCO-B-41310&external=true&parentUrl=close"
#     org_country : 'US'
#     org_currency : 'USD'
#     org_language : 'EN'

# attachments[]  : page_detail > File Attachments
#     file_name  : page_detail > File Attachments      Note:Don't take file extention
#     file_type  : page_detail > File Attachments      Note:Take only file extention
#     external_url  :  page_detail > File Attachments

# lot_detail[]  : page_detail > Item Information
#     lot_title : page_detail > NIGP Code     Note:Splite after numeric value..........Don't take numeric value
#     lot_quantity :  page_detail > Qty




#*******************************************************************************************************************************************************

# script_name:'us_nevadae_spn'

# urls:"https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"

# page_no:tender_html_element 	//*[@id="bidSearchResultsForm:bidResultId_data"]/tr 	10     

# performance_country:'US'

# currancy:'USD'	

# main_language:'EN'      

# procurement_method:2

# notice_type:4

# notice_no : tender_html_element > Bid Solicitation #              Note:If notice_no is not available then grab from notice_url

# local_title : tender_html_element > Description

# notice_deadline : tender_html_element > Bid Opening Date         Note:Grab time also

# notice_url : tander_html_element > Bid Solicitation #

# notice_text: page_detail 		Note:Take "tender_html_element" data also

# publish_date : page_detail > Available Date           Note:Grab time also

# document_opening_time : page_detail > 	Bid Opening Date

# document_type_description : page_detail > Retainage

# pre_bid_meeting_date: page_detail > Pre Bid Conference

# customer_detail[] > page_detail
#     org_name: page_detail > Organization
#     contact_person : tender_html_element > Buyer
#     org_address : page_detail > Location , Department
#     org_phone: page_detail  > Info Contact      Note:present than take          Ref_uel="https://nevadaepro.com/bso/external/bidDetail.sdo?docId=80DOT-S2679&external=true&parentUrl=close"
#     org_email: page_detail > Info Contact      Note:present than take           Ref_uel="https://nevadaepro.com/bso/external/bidDetail.sdo?docId=80DOT-S2679&external=true&parentUrl=close"
#     org_country : 'US'
#     org_currency : 'USD'
#     org_language : 'EN'

# attachments[]  : page_detail > File Attachments
#     file_name  : page_detail > File Attachments      Note:Don't take file extention
#     file_type  : page_detail > File Attachments      Note:Take only file extention
#     external_url  :  page_detail > File Attachments

# lot_detail[]  : page_detail > Item Information
#     lot_title : page_detail > NIGP Code     Note:Splite after numeric value..........Don't take numeric value
#     lot_quantity :  page_detail > Qty


#*******************************************************************************************************************************************************

# script_name:'us_commbuys_spn'

# urls:"https://www.commbuys.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"

# page_no:tender_html_element 	//*[@id="bidSearchResultsForm:bidResultId_data"]/tr 	10     

# performance_country:'US'

# currancy:'USD'	

# main_language:'EN'      

# procurement_method:2

# notice_type:4

# notice_no : tender_html_element > Bid Solicitation #              Note:If notice_no is not available then grab from notice_url

# local_title : tender_html_element > Description

# notice_deadline : tender_html_element > Bid Opening Date         Note:Grab time also

# notice_url : tander_html_element > Bid Solicitation #

# notice_text: page_detail 		Note:Take "tender_html_element" data also

# publish_date : page_detail > Available Date           Note:Grab time also

# document_opening_time : page_detail > 	Bid Opening Date

# document_purchase_start_time: page_detail > Blanket/Contract

# document_purchase_end_time : page_detail > Blanket/Contract End Date

# document_type_description : page_detail > Retainage

# pre_bid_meeting_date: page_detail > Pre Bid Conference

# customer_detail[] > page_detail
#     org_name: page_detail > Organization
#     contact_person : tender_html_element > Buyer
#     org_address : page_detail > Location , Department
#     org_phone: page_detail  > Info Contact      Note:present than take          
#     org_email: page_detail > Info Contact      Note:present than take           Ref_uel="https://www.commbuys.com/bso/external/bidDetail.sdo?docId=BD-24-1026-DOE02-DOE01-97984&external=true&parentUrl=close"
#     org_country : 'US'
#     org_currency : 'USD'
#     org_language : 'EN'

# attachments[]  : page_detail > File Attachments
#     file_name  : page_detail > File Attachments      Note:Don't take file extention
#     file_type  : page_detail > File Attachments      Note:Take only file extention
#     external_url  :  page_detail > File Attachments

# lot_detail[]  : page_detail > Item Information
#     lot_title : page_detail > NIGP Code     Note:Splite after numeric value..........Don't take numeric value
#     lot_quantity :  page_detail > Qty


    