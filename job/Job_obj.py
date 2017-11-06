from conn import connect_db


class Job_search:
    def __init__(self):
        self.conn, self.cursor = connect_db()
        self.keys = {"id", "title", "workType", "subClassification", "listingDate"}
        self.total = -1

    def find(self, offset, per_page, q=True, keywords={}):
        s = self.keyword_gen(keywords)
        if self.total < 0:
            self.cursor.execute("SELECT COUNT(*) FROM(SELECT * FROM jobs {:} LIMIT 200) AS n".format(*tuple(s)))
            self.total = self.cursor.fetchone()[0]
        s.extend([per_page, offset])
        self.cursor.execute("SELECT id,title,teaser,bulletPoints,workType,subClassification,listingDate,salary "
                            "FROM jobs {:} "
                            "ORDER BY listingDate DESC "
                            "LIMIT {:} OFFSET {:}".format(*tuple(s)))

        row = self.cursor.fetchall()

        ks = ["id", "title", "teaser", "bulletPoints", "workType", "subClassification", "listingDate", "salary"]
        if q:
            self.cursor.execute("SELECT workType FROM workType")
            fk1 = self.cursor.fetchall()
            self.cursor.execute("SELECT subClassification FROM subClassification")
            fk2 = self.cursor.fetchall()
            return [dict(zip(ks, d)) for d in row], fk1, fk2
        else:
            return [dict(zip(ks, d)) for d in row]

    def keyword_gen(self, keyword_dict):
        s = []
        for k, v in keyword_dict.items():
            if k in self.keys:
                if k == "listingDate":  # value of listingDate : tuple(startDate, endDate)
                    s.append("(listingDate Between '{:}' AND '{:}')".format(v[0], v[1]))
                else:
                    s.append("{:}='{:}'".format(k, v))
        if s:
            return ["WHERE " + " AND ".join(s)]
        else:
            return [""]


if __name__ == '__main__':
    j = Job_search()
    print(j.find(10, 5, {"listingDate": ("2017-10-25", "2017-10-30")}))
