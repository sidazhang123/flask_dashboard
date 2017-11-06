import mysql.connector


def connect_db():
    conn = mysql.connector.connect(user='root', database="seek_jobs", password='dazar123')
    return conn, conn.cursor()


mysql_err = mysql.connector.Error
