import psycopg2
import psycopg2.extras
from typing import TypedDict

class Users(TypedDict):
    name: str
    password: bytes
    salt: bytes
    public_key: str

class NoDataFoundError(Exception):
    """Exception for handling ```None``` returns from database."""

    def __init__(self, message="No data found in the database.") -> None:
        super().__init__(message)
 

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
        if hasattr(self, "conn"):
            self.conn.close()

    def get_user(self, name: str) -> Users:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT * FROM public.users WHERE name = %s", 
            (name,)
        )
        user = cur.fetchone()
        cur.close()
        if user is None:
            raise NoDataFoundError
        row: Users = {
            "name": user["name"],
            "password": user["password"],
            "salt": user["salt"],
            "public_key": user["public_key"]
        }
        return row
    
    def get_pubkey(self, name: str) -> bytes:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT public_key FROM public.users WHERE name = %s", 
            (name,)
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            raise NoDataFoundError
        return row[0].encode()


    def get_by_pubkey(self, public_key: bytes) -> str:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT name FROM public.users WHERE public_key = %s",
            (public_key.decode(),)
        )
        user = cur.fetchone()
        if user is None:
            raise NoDataFoundError
        cur.close()
        return user[0]

    def get_all_users(self):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM public.users"
        )
        users = cur.fetchall()
        cur.close()
        return users

    def add_user(self, name: str, password: bytes, 
                 salt: bytes, public_key: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (name, password, salt, public_key) VALUES (%s, %s, %s, %s)", 
            (name, psycopg2.Binary(password), psycopg2.Binary(salt), public_key)
        )
        self.conn.commit()
        cur.close()