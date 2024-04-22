import gec_common.common_eprocure as common_eprocure

script_name = 'in_goa'

domain_url = 'https://eprocure.goa.gov.in/nicgep'

org_state = 'Goa'

common_eprocure.eprocure(script_name,domain_url,org_state)