import psycopg2
import psycopg2.extras

def connect(password):
    conn = psycopg2.connect(
        database="Chat-project", 
        user="postgres", 
        password=password, 
        host="localhost", 
        port="5432"
        )
    return conn

def get_user(conn, name , values="*"):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        f"SELECT {values} FROM public.users WHERE name = %s", 
        (name,)
        )
    user = cur.fetchone()
    cur.close()
    return user

def get_by_pubkey(conn, public_key):
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM public.users WHERE public_key = %s",
        (public_key.decode('utf-8'))
    )
    user = cur.fetchone()
    cur.close()
    return user[0] if user else None

def get_all_users(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM public.users"
    )
    users = cur.fetchall()
    cur.close()
    return users

def add_user(conn, name, password, salt, public_key):
    cur = conn.cursor()
    cur.execute(
    "INSERT INTO users (name, password, salt, public_key) VALUES (%s, %s, %s, %s)", 
    (name, psycopg2.Binary(password), psycopg2.Binary(salt), public_key.decode('utf-8'))
)
    conn.commit()
    cur.close()