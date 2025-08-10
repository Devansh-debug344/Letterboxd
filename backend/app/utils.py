from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'] , deprecated = "auto")

def hash_password(password : str):
    return pwd_context.hash(password)

def verify_password(non_hash_password : str , hash_password :str):
    return pwd_context.verify(non_hash_password , hash_password)

