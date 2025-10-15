# top-level imports
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EmailEncryptor:
    def __init__(self, secret_key: str, salt: bytes = None):
        """
        Initialize the encryptor with a secret key and optional salt
        
        :param secret_key: A strong, secret passphrase
        :param salt: Optional cryptographic salt (generated if not provided)
        """
        # Validate secret key
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Generate or use provided salt
        self.salt = salt or os.urandom(16)
        # Store secret key for reuse during decryption
        self.secret_key = secret_key
        
        # Derive a strong encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000  # High iteration count for security
        )
        derived_key = base64.urlsafe_b64encode(
            kdf.derive(secret_key.encode('utf-8'))
        )
        
        # Create Fernet cipher suite
        self.cipher_suite = Fernet(derived_key)

    def encrypt(self, email_blurb: str) -> str:
        """
        Encrypt the entire email blurb
        
        :param email_blurb: Text to encrypt
        :return: Base64 encoded encrypted string
        """
        try:
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(email_blurb.encode('utf-8'))
            # Return the Fernet token as-is (already urlsafe base64)
            return {
                'encrypted_payload': encrypted_data.decode('utf-8'),
                'salt': base64.b64encode(self.salt).decode('utf-8')
            }
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_payload: dict) -> str:
        """
        Decrypt the entire email blurb
        
        :param encrypted_payload: Base64 encoded encrypted string
        :return: Decrypted string
        """
        # Decode the salt; DO NOT base64-decode the token itself
        salt = base64.b64decode(encrypted_payload['salt'])
        encrypted_token = encrypted_payload['encrypted_payload'].encode('utf-8')

        # Recreate the cipher suite with the original salt and same secret key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        derived_key = base64.urlsafe_b64encode(
            kdf.derive(self.secret_key.encode('utf-8'))
        )
        cipher_suite = Fernet(derived_key)

        decrypted_data = cipher_suite.decrypt(encrypted_token)
        return decrypted_data.decode('utf-8')

class EncryptionError(Exception):
    """Custom exception for encryption errors"""
    pass

class DecryptionError(Exception):
    """Custom exception for decryption errors"""
    pass

# Example Usage
def main():
    # Import here to avoid NameError and load the local .env
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

    # Use the stable key from .env
    secret_key = os.getenv("AES_SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        raise SystemExit("AES_SECRET_KEY missing or too short in Backend/.env")

    # Create encryptor with the env-provided secret
    encryptor = EmailEncryptor(secret_key)
    
    # Sample email blurb
    email_blurb = """
    FW: DIC Submission Clinica Msr. Oscar A. Romero eff 10/01/24
    1 message
    Joel Ramirez <Joel@goldenbear.com> Thu, Sep 19, 2024 at 11:16 AM
    To: "galvisf@resiquant.ai" <galvisf@resiquant.ai>
    No Kanverse email/SOV provided due to being only pdf attachments.
    Pulled data from the first attachment: FILE SUMMARY.PDF
    """
    
    # Encrypt
    encrypted = encryptor.encrypt(email_blurb)
    print("Encrypted:", encrypted)
    
    # Decrypt
    decrypted = encryptor.decrypt(encrypted)
    print("Decrypted:", decrypted)
    
    # Verify
    assert decrypted == email_blurb, "Decryption failed"

if __name__ == "__main__":
    main()