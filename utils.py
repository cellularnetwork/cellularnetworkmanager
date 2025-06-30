
import sqlite3

def get_database_path(username):
    if username == "titolare":
        return "databases/titolare.db"
    elif username.startswith("manager_"):
        nome_negozio = username.split('_')[1]
        return f"databases/{nome_negozio}.db"
    return "databases/titolare.db"

def get_user_from_db(username, password):
    db_path = get_database_path(username)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[1] == password:
        return True
    return False
