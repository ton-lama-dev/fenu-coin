import sqlite3

from main import get_username_by_id


ids = [495785251,761860971,764230762,838066507,859119916,908618552,1442113220,1587202101,1685811511,1807507247,2121995893,5144279110,5714211566,6079104664,6257396100,6312417965,6336089413,6796122908,6982862545,7278076790]
usernames = [get_username_by_id(id) for id in ids]
balanses = [1.5,2.5,1.5,1.5,1,1,1.5,2.5,2.5,1.5,2.5,1.5,1.5,1.5,1.5,2,1,4.5,2.5,1.5]
referrals = [0,0,0,0,0,0,0,1,1,1,0,0,3,0,0,0,0,6,0,0]
referrers = [1685811511,6796122908,5714211566,6796122908,None,1587202101,5714211566,None,6796122908,5714211566,6796122908,1807507247,6796122908,None,None,None,6796122908,None,None,None]
wallets = [None,None,None,None,None,None,None,None,"UQBFycHl4YAx_4Qx-SU-IlW7066S9CJEwEpLTgN-Wg6P7lH-",None,None,None,None,None,None,None,None,None,None,None]
last_claims = ["2024-08-20 20:23:05","2024-08-22 08:06:26","2024-08-22 11:44:22","2024-08-20 15:32:35","2000-01-01 00:00:00","2000-01-01 00:00:00","2024-08-22 05:49:01","2024-08-22 07:09:50","2024-08-22 04:22:57","2024-08-22 05:09:27","2024-08-22 08:35:41","2024-08-22 07:08:06","2024-08-22 05:01:58","2024-08-20 11:35:39","2024-08-19 16:49:11","2024-08-22 04:21:46","2000-01-01 00:00:00","2024-08-22 04:22:15","2024-08-22 04:23:01","2024-08-20 15:13:52"]
registration_dates = ["2024-08-20 19:53:25","2024-08-20 15:03:42","2024-08-22 11:42:19","2024-08-20 15:31:09","2024-08-20 18:36:15","2024-08-22 07:11:47","2024-08-22 05:47:04","2024-08-19 15:27:58","2024-08-20 14:55:50","2024-08-22 05:06:09","2024-08-20 16:00:54","2024-08-22 07:06:14","2024-08-22 05:01:27","2024-08-20 11:34:10","2024-08-19 13:02:20","2024-08-19 12:03:33","2024-08-21 06:23:30","2024-08-19 12:03:55","2024-08-19 15:31:24","2024-08-20 15:13:35"]
languages = ["ru","ru","ru","ru","ru","ru","ru","ru","ru","ru","ru","ru","ru","ru","en","en","ru","ru","ru","ru"]


def connect_db():
    return sqlite3.connect("data.db")


def insert(id, username, balance, referrals, referrer, wallet, last_claim, registration_date, language):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, username, balance, referrals, referrer, wallet, last_claim, registration_date, language) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, username, balance, referrals, referrer, wallet, last_claim, registration_date, language))
        conn.commit()


for i in range(len(ids)):
    insert(id=ids[i], username=usernames[i], balance=balanses[i], referrals=referrals[i], referrer=referrers[i], wallet=wallets[i], last_claim=last_claims[i], registration_date=registration_dates[i], language=languages[i])        
