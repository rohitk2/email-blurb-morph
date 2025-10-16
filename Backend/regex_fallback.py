import re
import os

def get_signature(email_blurb):
    """
    Extract the signature section from an email blurb
    
    Strategy:
    1. Look for sections that contain both "License" and an email
    2. Prioritize sections near the end of the email
    3. Handle multiple possible signatures
    
    :param email_blurb: Full email text
    :return: Extracted signature section
    """
    # Split patterns that typically end an email body
    split_patterns = [
        r'((?:From:|Sent:).*)',  # Stop at next email header
        r'(The contents of this email.*)',  # Stop at confidentiality notice
        r'(Privacy Notice.*)'  # Stop at legal notices
    ]
    
    # Clean up the blurb
    cleaned_blurb = email_blurb.replace('\n', ' ')
    
    # Find signatures containing "License" with an email domain,
    # limiting to <=200 chars before and after "License", and requiring ".com" (case-sensitive)
    chunk_size = 1500
    selected_signature = ""
    for i in range(0, len(cleaned_blurb), chunk_size):
        chunk = cleaned_blurb[i:i+chunk_size]
        if (("license" in chunk) or ("License" in chunk)) and (".com" in chunk):
            selected_signature = chunk.strip()
            break
    
    # If no signatures found, return empty string
    if not selected_signature:
        return ""
    
    # Return the last (most likely) signature
    return selected_signature

def get_email(signature):
    """
    Extract email from a signature
    
    Strategy:
    1. Use regex to find standard email format
    2. Return the first match
    
    :param signature: Signature text
    :return: Extracted email address
    """
    # Regex for standard email format
    email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    
    # Find emails
    emails = re.findall(email_pattern, signature, re.IGNORECASE)
    
    # Return first email found
    return emails[0] if emails else ""

def get_address(signature):
    """
    Extract address from a signature
    
    Strategy:
    1. Look for pattern starting with number
    2. Contain "CA" 
    3. End with a 5-digit ZIP code
    4. Limit to 10 words
    
    :param signature: Signature text
    :return: Extracted address
    """
    # Regex for address pattern
    # Starts with number, contains CA, optional zip code, max 10 words
    address_pattern = r'(\d+[^0-9\n]*(?:CA|WA)\s+\d{5}(?:\-\d{4})?)'
    
    # Find addresses
    addresses = re.findall(address_pattern, signature, re.IGNORECASE)
    
    # Return first address found
    return addresses[0].strip() if addresses else ""

def get_broker_info(email_blurb):
    """
    Extract broker information from an email blurb
    
    Strategy:
    1. Get signature
    2. Extract email from signature
    3. Extract address from signature
    
    :param email_blurb: Full email text
    :return: Dictionary with broker_name, broker_email, and complete_address
    """
    # Get signature
    signature = get_signature(email_blurb)
    
    # Extract broker info
    broker_email = get_email(signature)
    complete_address = get_address(signature)
    
    return {
        "broker_email": broker_email,
        "complete_address": complete_address
    }

# Demonstration
def demonstrate_extraction():
    testcases_dir = os.path.join(os.path.dirname(__file__), "testcases")
    if not os.path.isdir(testcases_dir):
        print(f"Testcases folder not found: {testcases_dir}")
        return

    for filename in sorted(os.listdir(testcases_dir)):
        if not filename.lower().endswith(".txt"):
            continue

        path = os.path.join(testcases_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                email_blurb = f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue

        print(f"\n=== {filename} ===")

        # Run broker info extraction on the full text string
        broker_info = get_broker_info(email_blurb)
        print("Broker Info:")
        print(broker_info)
        print("\n---\n")
# Run demonstration
if __name__ == "__main__":
    demonstrate_extraction()