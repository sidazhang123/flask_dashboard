import sys
import urllib3
import certifi
import json
from datetime import datetime
import mysql.connector


# Grab Sydney ICT job info in a specified range of time from api of seek.com.au.
# Store in mysql with fulltext index
class Job:
    def __init__(self):
        # 11f646dd685b42a4314cccdc28a98f834b485ca0f5ae523c
        self.cnx = mysql.connector.connect(user='root', database="seek_jobs", password='dazar123')
        self.cursor = self.cnx.cursor()
        self.url = 'https://jobsearch-api.cloud.seek.com.au/search?siteKey=AU-Main&whe' \
                   're=All%20Sydney%20NSW&classification=6281&sourcesystem=houston&page='
        self.interested_field = ['id', 'title', 'teaser', 'bulletPoints', 'workType', 'subClassification', 'area',
                                 'advertiser', 'isPremium', 'isStandOut', 'listingDate', 'salary']
        self.interested_term = {}
        self.fk_tables = {'workType': [],
                          'area': [],
                          'subClassification': []
                          }
        self.init_fk_tables()

    # To mitigate data duplication, only create non-existing frequent items
    def init_fk_tables(self):
        for i in self.fk_tables.keys():
            self.cursor.execute("SELECT {} FROM {}".format(i, i.lower()))
            for (col_2) in self.cursor:
                self.fk_tables[i].append(col_2)

    def check_fk_table(self, table_name, to_insert):
        for idx, col_2 in enumerate(self.fk_tables[table_name]):
            # print('id: {}, col_2: {}, to_insert: {}, equal{}'.format(idx,col_2,to_insert, col_2==to_insert))
            if col_2 == to_insert:
                # print('old id:'+str(idx))
                return idx, True
        # print('new rec return: {}'.format(len(self.fk_tables[table_name])))
        return len(self.fk_tables[table_name]), False

    def grab_page(self, page_id):

        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        r = http.request('GET', self.url + page_id)
        print("grab")
        return json.loads(r.data.decode('utf-8'))

    def parse_and_save_db(self, json, in_hours):
        print("parse")
        col_names = ','.join(self.interested_field)
        now = datetime.utcnow()
        insert_vars = []
        # self.cursor.execute("SELECT MAX(listingDate) from jobs")
        # latest_record = self.cursor.fetchone()
        # if latest_record:
        #     latest_record=latest_record[0]
        for job in json['data']:
            listing_date = job['listingDate'].replace('T', ' ').replace('Z', '')

            hour_diff = (now - datetime.strptime(listing_date, '%Y-%m-%d %H:%M:%S')).total_seconds()/3600
            print("hour_diff: "+str(hour_diff))
            # Halt when listingDate exceeds designated time range
            if hour_diff >= in_hours and str(job['isPremium']) == 'False':
                return False
            # if latest_record and datetime.strptime(listing_date, '%Y-%m-%d %H:%M:%S')<= latest_record:
            #     continue
            # Format raw data
            for i in self.interested_field:
                if i not in self.fk_tables.keys():
                    s = str(job[i])
                    if s == 'True':
                        insert_vars.append(1)
                    elif s == 'False':
                        insert_vars.append(0)
                    elif i == 'listingDate':
                        insert_vars.append(listing_date)
                    elif i == 'advertiser':
                        insert_vars.append(job[i]['description'])
                    else:
                        insert_vars.append(s)
                else:
                    if i.startswith('sub'):
                        to_insert = job[i]['description']
                    else:
                        to_insert = job[i]
                    id, in_tab = self.check_fk_table(i, to_insert)

                    if not in_tab:
                        self.fk_tables[i].append(to_insert)
                        self.cursor.execute("INSERT INTO {} (id{},{}) VALUES(%s,%s)".format(i.lower(), i, i), (id, to_insert))
                    insert_vars.append(id)

            try:
                self.cursor.execute("INSERT INTO jobs ({}) VALUES({})".format(col_names,
                                                                              ','.join(['%s' for i in range(
                                                                                  len(self.interested_field))])),
                                    tuple(insert_vars))
                print("INSERTED one job")
            except mysql.connector.Error as e:
                if e.errno == 1062 and e.sqlstate == 23000:  # indicate duplicate inputs
                    print('dup records')
                else:
                    print(e)

            insert_vars = []
        self.cnx.commit()
        return True

    def page_turning(self, in_hours=2):
        page = 0
        ret = 'continue'
        while ret:
            page += 1
            page_json = self.grab_page(str(page))
            ret = self.parse_and_save_db(page_json, in_hours)


if __name__ == '__main__':
    job = Job()
    if len(sys.argv)>1:
        if sys.argv[1].isdigit():
            job.page_turning(int(sys.argv[1]))
        else:
            print('There must be only one argument and it must be integer.')
    else:
        job.page_turning(2)
    # job.page_turning(30*24)
