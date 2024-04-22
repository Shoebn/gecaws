import gec_common.common_eprocure as common_eprocure

script_name = 'in_sikkimtender'

domain_url = 'https://sikkimtender.gov.in/nicgep'

org_state = 'Sikkim'

common_eprocure.eprocure(script_name,domain_url,org_state)
