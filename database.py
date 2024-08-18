import sqlite3
from datetime import datetime

import config


def connect_db():
    return sqlite3.connect("data.db")


def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS users(
                       id INTEGER PRIMARY KEY,
                       balance INTEGER DEFAULT {config.WELCOME_BONUS},
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
            balance INTEGER DEFAULT {config.WELCOME_BONUS},
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
        current_balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id, )).fetchone()[0]
        new_balance = current_balance + int(number)
        cursor.execute(f"UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))


def reward_user_for_subscription(user_id: int, reward: int):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id, ))
        new_balance = int(cursor.fetchone()[0]) + reward
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))


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
        new_balance = int(cursor.fetchone()[0]) + config.REFERRAL_REWARD
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
        
        standard_columns = {'id', 'balance', 'referrer_id', 'referrals', 'wallet'}
        task_columns = [info[1] for info in columns_info if info[1] not in standard_columns]
        
        cursor.execute(f"SELECT {', '.join(task_columns)} FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        available_tasks = [task for task, value in zip(task_columns, user_data) if value == 0]

        available_tasks_links = []
        for task in available_tasks:
            with connect_db() as conn:
                cursor = conn.cursor()
                task = "@" + task
                cursor.execute("SELECT private_link FROM channels WHERE public_link = ?", (task, ))
                task_link = cursor.fetchone()[0]
                available_tasks_links.append(task_link)
        
        return dict(zip(available_tasks, available_tasks_links))


def get_reward(public_link: str) -> int:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reward FROM channels WHERE public_link = ?", (public_link, ))
        print(public_link)
        result = cursor.fetchone()
        print(result)
        print(result[0])
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


def add_user_into_db(user_id, language, referrer=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, language, referrer) VALUES (?, ?, ?)", (user_id, language, referrer))
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
    

def get_referrals(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referrals FROM users WHERE id = ?", (user_id,))
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
    

def get_user_info(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, balance, referrals, referrer, wallet, registration_date, language FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchall()[0]
        #lst = [i[0] for i in row]
        return row


def users_set(user_id: int, item: str, value):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {item} = ? WHERE id = ?", (value, user_id))
        conn.commit()
