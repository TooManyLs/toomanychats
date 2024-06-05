import psycopg2
import psycopg2.extras
from typing import TypedDict

class Users(TypedDict):
    name: str
    password: bytes
    salt: bytes
    public_key: str
 

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

    def get_user(self, name: str) -> Users | None:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT * FROM public.users WHERE name = %s", 
            (name,)
        )
        user = cur.fetchone()
        cur.close()
        if user:
            row: Users = {
                "name": user["name"],
                "password": user["password"],
                "salt": user["salt"],
                "public_key": user["public_key"]
            }
            return row
    
    def get_pubkey(self, name: str) -> bytes | None:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT public_key FROM public.users WHERE name = %s", 
            (name,)
        )
        row = cur.fetchone()
        cur.close()
        if row:
            return row[0].encode()


    def get_by_pubkey(self, public_key):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT name FROM public.users WHERE public_key = %s",
            (public_key.decode('utf-8'))
        )
        user = cur.fetchone()
        cur.close()
        return user["name"] if user else None

    def get_all_users(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM public.users"
        )
        users = cur.fetchall()
        cur.close()
        return users

    def add_user(self, name: str, password: bytes, 
                 salt: bytes, public_key: bytes) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (name, password, salt, public_key) VALUES (%s, %s, %s, %s)", 
            (name, psycopg2.Binary(password), psycopg2.Binary(salt), public_key.decode('utf-8'))
        )
        self.conn.commit()
        cur.close()