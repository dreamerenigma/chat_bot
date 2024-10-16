import random
import string


def generate_token() -> str:
    """Generates a random token of length 35 using letters and digits."""
    token_secret = ''.join(random.choices(string.ascii_letters + string.digits, k=35))
    return token_secret
