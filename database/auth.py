import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
      return False

    if not hashed_password.startswith("$2"):
      return plain_password == hashed_password

    try:
      return bcrypt.checkpw(
          plain_password.encode(), hashed_password.encode()
      )
    except ValueError:
      return plain_password == hashed_password