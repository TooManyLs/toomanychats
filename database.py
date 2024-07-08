import os

import psycopg2
import psycopg2.extras
from typing import TypedDict

class Users(TypedDict):
    name: str
    password: bytes
    salt: bytes
    totp_secret: str

class NoDataFoundError(Exception):
    """Exception for handling ```None``` returns from database."""

    def __init__(self, message="No data found in the database.") -> None:
        super().__init__(message)
 

class Connect:
    def __enter__(self):
        self.conn = psycopg2.connect(
            database="Chat-project", 
            user="postgres", 
            password=os.getenv("DB_PASS"), 
            host="localhost", 
            port="5432"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "conn"):
            self.conn.close()
    
    def get_user(self, name: str, device_id: bytes = b"none") -> tuple[Users, str]:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            SELECT u.name, u.password, u.salt, u.totp_secret, 
                COALESCE(uk.public_key, '0') AS public_key
            FROM public."Users" u
            LEFT JOIN public."UserKeys" uk ON u.user_id = uk.user_id
            WHERE u.name = %s AND uk.device_id = %s
            """,
            (name, psycopg2.Binary(device_id))
        )
        user = cur.fetchone()
        cur.close()

        if user is None:
            raise NoDataFoundError

        user_data: Users = {
            "name": user["name"],
            "password": user["password"],
            "salt": user["salt"],
            "totp_secret": user["totp_secret"]
        }

        return user_data, user["public_key"]
    
    def get_pubkey(self, name: str) -> bytes:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            SELECT uk.public_key
            FROM public."UserKeys" uk
            JOIN public."Users" u ON uk.user_id = u.user_id
            WHERE u.name = %s
            """,
            (name,)
        )
        row = cur.fetchone()
        if row is None:
            raise NoDataFoundError
        
        cur.close()
        return row[0].encode()


    def get_by_pubkey(self, public_key: str) -> str:
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            SELECT u.name
            FROM public."UserKeys" uk
            JOIN public."Users" u ON uk.user_id = u.user_id
            WHERE uk.public_key = %s
            """,
            (public_key,)
        )
        user = cur.fetchone()
        if user is None:
            raise NoDataFoundError
        
        cur.close()
        return user[0]

    def add_user(self, name:str, password: bytes, 
                  salt: bytes, secret: str, 
                  device_id: bytes, public_key: str) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """INSERT INTO public."Users" (name, password, salt, totp_secret) 
            VALUES (%s, %s, %s, %s)""",
            (name, psycopg2.Binary(password), psycopg2.Binary(salt), secret)
        )
        self.conn.commit()
        cur.close()

        self.add_device(name, device_id, public_key)
        

    def add_device(self, name:str, device_id: bytes, public_key: str) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """INSERT INTO public."UserKeys" (device_id, user_id, public_key)
            VALUES (%s, (SELECT user_id FROM public."Users" WHERE name = %s), %s)""",
            (psycopg2.Binary(device_id), name, public_key)
        )
        self.conn.commit()
        cur.close()