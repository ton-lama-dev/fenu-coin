import sqlite3
from datetime import datetime

import config
from main import get_username_by_id


def connect_db():
    return sqlite3.connect("data.db")


def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS users(
                       id INTEGER PRIMARY KEY,
                       username TEXT,
                       balance INTEGER DEFAULT {config.WELCOME_BONUS},
                       buyers_balance INTEGER DEFAULT 0,
                       paid_balance INTEGER DEFAULT 0,
                       referrals INTEGER DEFAULT 0,
                       referrer INTEGER,
                       wallet TEXT DEFAULT 'не подключен',
                       last_claim TIMESTAMP DEFAULT '2000-01-01 00:00:00',
                       registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                       language TEXT DEFAULT 'ru')
                       """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS channels(
                       public_link TEXT,
                       private_link TEXT,
                       done_times INTEGER DEFAULT 0,
                       reward INTEGER DEFAULT 100)
                       """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS buyers(
                       username TEXT,
                       wallet TEXT,
                       sum INTEGER)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawal_requests(
                       username TEXT,
                       amount INTEGER,
                       wallet TEXT)""")
        conn.commit()


def add_channel_into_db(public_link, private_link, reward=100):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE users ADD COLUMN {public_link[1:]} INTEGER DEFAULT 0")
        cursor.execute(f"INSERT INTO channels (public_link, private_link, reward) VALUES (?, ?, ?)", (public_link, private_link, reward))
        conn.commit()


def remove_channel_from_db(public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        columns = [info[1] for info in columns_info if info[1] != public_link[1:]]
        
        columns_str = ", ".join(columns)
        
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users_new(
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT {config.WELCOME_BONUS},
            buyers_balance INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referrer INTEGER,
            wallet TEXT DEFAULT 'не подключен',
            last_claim TIMESTAMP DEFAULT '2000-01-01 00:00:00',
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            language TEXT DEFAULT 'ru')
        """)
        
        cursor.execute(f"INSERT INTO users_new ({columns_str}) SELECT {columns_str} FROM users")
        
        cursor.execute("DROP TABLE users")
        
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        cursor.execute(f"DELETE FROM channels WHERE public_link = ?", (public_link, ))
        
        conn.commit()


def is_channel_in_db(column_name):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]
        return column_name[1:] in column_names


def subscribe_user_to_channel(user_id, public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {public_link[1:]} = 1 WHERE id = ?", (user_id, ))


def increase_task_done_times(public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        current_done_times = cursor.execute("SELECT done_times FROM channels WHERE public_link = ?", (public_link, )).fetchone()[0]
        new_done_times = current_done_times + 1
        cursor.execute(f"UPDATE channels SET done_times = ? WHERE public_link = ?", (new_done_times, public_link))


def increase_user_balance(user_id, number):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id, ))
        current_balance = cursor.fetchone()[0]
        new_balance = current_balance + float(number)
        cursor.execute(f"UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        conn.commit()


def decrease_user_balance(user_id, number):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id, ))
        current_balance = cursor.fetchone()[0]
        new_balance = current_balance - float(number)
        cursor.execute(f"UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        conn.commit()


def reward_user_for_subscription(user_id: int, reward: int):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id, ))
        new_balance = int(cursor.fetchone()[0]) + reward
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        conn.commit()


def reward_buyer_referrer(referrer_id: int, amount: int):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT buyers_balance FROM users WHERE id = ?", (referrer_id, ))
        data = cursor.fetchone()
        new_balance = float(data[0]) + amount
        cursor.execute("UPDATE users SET buyers_balance = ? WHERE id = ?", (new_balance, referrer_id))
        conn.commit()


def create_withdrawal_request(user_id: float):
    with connect_db() as conn:
        cursor = conn.cursor()
        username = get_username_by_id(user_id)
        amount = round(float(users_get(item="buyers_balance", user_id=user_id)), 2)
        if amount <= 0:
            raise Exception("Not enough funds")
        wallet = get_wallet(user_id=user_id)
        cursor.execute("INSERT INTO withdrawal_requests (username, amount, wallet) VALUES (?, ?, ?)", (username, amount, wallet))

        cursor.execute("UPDATE users SET buyers_balance = 0 WHERE id = ?", (user_id, ))
        conn.commit()


def increase_referrals(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referrals FROM users WHERE id = ?", (user_id, ))
        new_referrals = int(cursor.fetchone()[0]) + 1
        cursor.execute("UPDATE users SET referrals = ? WHERE id = ?", (new_referrals, user_id))


def update_wallet(user_id, wallet):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET wallet = ? WHERE id = ?", (wallet, user_id))


def send_reward_to_referrer(referrer_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (referrer_id, ))
        new_balance = float(cursor.fetchone()[0]) + config.REFERRAL_REWARD
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, referrer_id))


def get_channel_private_link(public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT private_link FROM channels WHERE public_link = ?", (public_link, ))
        private_link = cursor.fetchone()[0]
        return private_link


def get_available_tasks(user_id) -> dict:
    with connect_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        
        standard_columns = {
            "id",
            "username",
            "balance",
            "buyers_balance",
            "referrals",
            "referrer",
            "wallet",
            "last_claim",
            "registration_date",
            "language",
            "paid_balance",
        }
        task_columns = [info[1] for info in columns_info if info[1] not in standard_columns]
        if task_columns:
            cursor.execute(f"SELECT {', '.join(task_columns)} FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            available_tasks = [task for task, value in zip(task_columns, user_data) if value == 0]

            if available_tasks:
                available_tasks_links = []
                for task in available_tasks:
                    with connect_db() as conn:
                        cursor = conn.cursor()
                        task = "@" + task
                        cursor.execute("SELECT private_link FROM channels WHERE public_link = ?", (task, ))
                        task_link = cursor.fetchone()[0]
                        available_tasks_links.append(task_link)
                
                return dict(zip(available_tasks, available_tasks_links))
            else:
                return {}
        else:
            return {}


def get_reward(public_link: str) -> int:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reward FROM channels WHERE public_link = ?", (public_link, ))
        result = cursor.fetchone()
        return result[0]


def get_last_claim(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_claim FROM users WHERE id = ?", (user_id, ))
        last_claim = cursor.fetchone()[0]
        result = datetime.strptime(last_claim, '%Y-%m-%d %H:%M:%S')
        return result


def get_times_done(public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT done_times FROM channels WHERE public_link = ?", (public_link, ))
        return cursor.fetchone()[0]


def claim_reward(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        new_balance = get_balance(user_id=user_id) + config.CLAIM_REWARD
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE users SET balance = ?, last_claim = ? WHERE id = ?", (new_balance, current_time, user_id))


def add_user_into_db(user_id, language, username, referrer=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, language, username, referrer) VALUES (?, ?, ?, ?)", (user_id, language, username, referrer))
        conn.commit()


def add_buyer_into_db(username: str, sum, wallet=None) -> None:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO buyers (username, sum, wallet) VALUES (?, ?, ?)", (username, sum, wallet))
        conn.commit()


def is_user_in_db(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return True if cursor.fetchone() else False
    

def was_rewarded_for_subscription(user_id, public_link):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {public_link[1:]} FROM users WHERE id = ?", (user_id, ))
        result = cursor.fetchone()[0]
        return True if result == 1 or result is None else False


def get_wallet(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    

def get_referrals_ids(user_id: int) -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE referrer = ?", (user_id, ))
        data = cursor.fetchall()
        result = [i[0] for i in data]
        return result if data else None


def get_referrals_usernames(referrals_ids: list) -> list:
    if referrals_ids:
        usernames = [get_username_by_id(id) for id in referrals_ids]
        return usernames if usernames else None
    else:
        return []


def get_buyers_referrals_sums(usernames: list) -> list[tuple]:
    with connect_db() as conn:
        cursor = conn.cursor()
        result = list()
        for username in usernames:
            cursor.execute("SELECT sum FROM buyers WHERE username = ?", (username, ))
            data = cursor.fetchone()
            if data:
                num = float(data)
                result.append(num)
            else:
                result.append(0)
        return result if result else None


def get_referrals(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referrals FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    

def get_referrer_id(user_id: int) -> int:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referrer FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def get_balance(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    

def get_language(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()[0]
        return result
    

def get_number_of_users():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count


def get_withdrawal_requests_data() -> list[tuple]:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM withdrawal_requests")
        result = cursor.fetchall()
        return result if result else None


def get_all_users() -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users")
        answer = cursor.fetchall()
        result = [id[0] for id in answer]
        return result
    

def get_all_tasks() -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT public_link FROM channels")
        answer = cursor.fetchall()
        result = [id[0] for id in answer]
        return result
    

def get_all_registration_dates() -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT registration_date FROM users")
        answer = cursor.fetchall()
        lst = [reg_date[0] for reg_date in answer]
        new_lst = []
        for item in lst:
            date = datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
            new_lst.append(date)
        return new_lst
    

def get_all_tasks_done():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT done_times FROM channels")
        answer = cursor.fetchall()
        result = [i[0] for i in answer]
        return result
    

def get_all_balances() -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users")
        answer = cursor.fetchall()
        result = [i[0] for i in answer]
        return result
    

def get_all_buyers() -> list:
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buyers")
    buyers = cursor.fetchall()
    conn.close()
    return buyers


def get_user_info(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, balance, referrals, referrer, wallet, registration_date, language FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchall()[0]
        #lst = [i[0] for i in row]
        return row


def get_user_id_by_username(username: str) -> int:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username, ))
        result = cursor.fetchone()
        if result != None:
            return result[0]
        else:
            return None


def users_set(user_id: int, item: str, value):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {item} = ? WHERE id = ?", (value, user_id))
        conn.commit()


def users_get(item: str, user_id: int):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {item} FROM users WHERE id = ?", (user_id, ))
        result = cursor.fetchone()
        if result != None:
            return result[0]
        else:
            return None


def users_increase(user_id: int, item: str, value: int):
    with connect_db() as conn:
        try:
            old_value = int(users_get(item=item, user_id=user_id))
            new_value = old_value + int(value)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {item} = ? WHERE id = ?", (new_value, user_id))
            conn.commit()
        except Exception as e:
            print(e)
