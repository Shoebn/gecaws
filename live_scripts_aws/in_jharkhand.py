import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_jharkhand'
log_config.log(SCRIPT_NAME)

domain_url = 'https://jharkhandtenders.gov.in/nicgep'

org_state = 'Jharkhand'

common_eprocure.eprocure(SCRIPT_NAME,domain_url,org_state)
