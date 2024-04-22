import psycopg2
# pip install psycopg2
from gec_common import web_application_properties
def get_conn():
    db = psycopg2.connect(user=web_application_properties.DATABASE_USERNAME,
                          password=web_application_properties.DATABASE_PASSWORD,
                          database=web_application_properties.DATABASE_NAME,
                          host=web_application_properties.DATABASE_HOST)
    return db
