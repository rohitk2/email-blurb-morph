import base64
import os
from dotenv import load_dotenv

def hash(text_blurb):
    # Load Backend/.env and get HASH_SECRET_KEY at call time
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path, override=True)
    key = os.getenv("HASH_SECRET_KEY")
    if not key:
        raise SystemExit("HASH_SECRET_KEY missing in Backend/.env")

    result = []
    key_len = len(key)

    for i, char in enumerate(text_blurb):
        key_char = key[i % key_len]
        encrypted_char = chr(ord(char) ^ ord(key_char))
        result.append(encrypted_char)

    encrypted = base64.b64encode(''.join(result).encode('utf-8'))
    return encrypted.decode('utf-8')

def unhash(encrypted_text_blurb):
    # Load Backend/.env and get HASH_SECRET_KEY at call time
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path, override=True)
    key = os.getenv("HASH_SECRET_KEY")
    if not key:
        raise SystemExit("HASH_SECRET_KEY missing in Backend/.env")

    encrypted = base64.b64decode(encrypted_text_blurb.encode('utf-8')).decode('utf-8')

    result = []
    key_len = len(key)

    for i, char in enumerate(encrypted):
        key_char = key[i % key_len]
        decrypted_char = chr(ord(char) ^ ord(key_char))
        result.append(decrypted_char)

    return ''.join(result)

# Example usage
if __name__ == "__main__":
    email_text = "This is a confidential email message with signature."
    # Test the functions
    encrypted = hash(email_text)
    print(f"Original: {email_text}")
    print(f"Encrypted: {encrypted}")
    decrypted = unhash(encrypted)
    print(f"Decrypted: {decrypted}")
    assert email_text == decrypted, "Encryption/Decryption failed!"
    print("\n✓ Encryption and decryption working correctly!")