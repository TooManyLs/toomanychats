import psycopg2
import psycopg2.extras

class Connect:
    def __init__(self, password):
        self.password = password

    def __enter__(self):
        self.conn = psycopg2.connect(
        database="Chat-project", 
        user="postgres", 
        password=self.password, 
        host="localhost", 
        port="5432"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def get_user(self, name, values="*"):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"SELECT {values} FROM public.users WHERE name = %s", 
            (name,)
        )
        user = cur.fetchone()
        cur.close()
        return user

    def get_by_pubkey(self, public_key):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name FROM public.users WHERE public_key = %s",
            (public_key.decode('utf-8'))
        )
        user = cur.fetchone()
        cur.close()
        return user[0] if user else None

    def get_all_users(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM public.users"
        )
        users = cur.fetchall()
        cur.close()
        return users

    def add_user(self, name, password, salt, public_key):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (name, password, salt, public_key) VALUES (%s, %s, %s, %s)", 
            (name, psycopg2.Binary(password), psycopg2.Binary(salt), public_key.decode('utf-8'))
        )
        self.conn.commit()
        cur.close()