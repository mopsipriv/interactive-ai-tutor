import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

VALID_HASH = "$2b$12$qvXG5fAUK30bXKeNNc2VCen92fxSY8lap7wv1CNu3ASeoBjShZ9t2" # password123

async def fix_passwords():
    host = os.getenv("DB_HOST", "127.0.0.1")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "rootpassword")
    db = os.getenv("DB_NAME", "peppi_db")
    port = int(os.getenv("DB_PORT", 3306))

    print(f"Connecting to MySQL at {host}:{port} ({db})...")
    conn = await aiomysql.connect(host=host, port=port, user=user, password=password, db=db)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE teacher SET password_hash = %s", (VALID_HASH,))
        t_count = cur.rowcount
        await cur.execute("UPDATE student SET password_hash = %s", (VALID_HASH,))
        s_count = cur.rowcount
        await conn.commit()
    conn.close()
    print(f"Successfully updated {t_count} teachers and {s_count} students to default password 'password123'!")

if __name__ == "__main__":
    asyncio.run(fix_passwords())
