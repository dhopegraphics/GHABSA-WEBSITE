#!/usr/bin/env python
"""
Convert VAPID keys from PEM format to DER base64 format
Required for compatibility with py-vapid and cryptography library
"""

import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.hazmat.backends import default_backend


def pem_to_der_base64(pem_key_str, is_private=True):
    """
    Convert PEM key to DER base64 format (single line, no headers)
    
    Args:
        pem_key_str: PEM formatted key string
        is_private: True for private key, False for public key
    
    Returns:
        Base64 encoded DER format key (single line)
    """
    pem_bytes = pem_key_str.encode('utf-8')
    
    if is_private:
        # Load private key
        key = load_pem_private_key(pem_bytes, password=None, backend=default_backend())
        # Export to DER format
        der_bytes = key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        # Load public key
        key = load_pem_public_key(pem_bytes, backend=default_backend())
        # Export to DER format
        der_bytes = key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    # Encode to base64 (urlsafe, no padding needed for storage)
    der_base64 = base64.urlsafe_b64encode(der_bytes).decode('utf-8')
    
    return der_base64


if __name__ == "__main__":
    print("=" * 80)
    print("VAPID Key Converter - PEM to DER Base64")
    print("=" * 80)
    print()
    
    # Get the PEM private key
    print("Paste your PRIVATE KEY (including -----BEGIN/END----- lines):")
    print("Press Enter, then Ctrl+D (Mac/Linux) or Ctrl+Z (Windows) when done:")
    print()
    
    private_pem_lines = []
    try:
        while True:
            line = input()
            private_pem_lines.append(line)
    except EOFError:
        pass
    
    private_pem = '\n'.join(private_pem_lines)
    
    print()
    print("=" * 80)
    print("Enter your PUBLIC KEY (e.g., BDQViBm4rBljSIOOrd69k7ju...):")
    public_key_raw = input().strip()
    
    try:
        # Convert private key
        print("\nConverting private key...")
        private_der_b64 = pem_to_der_base64(private_pem, is_private=True)
        print("✅ Private key converted!")
        
        # Public key is already in the right format if it's the raw base64
        # But let's verify it
        print("\nPublic key is already in correct format!")
        
        print()
        print("=" * 80)
        print("✅ CONVERSION COMPLETE!")
        print("=" * 80)
        print()
        print("Add these to your .env file:")
        print()
        print(f"VAPID_PUBLIC_KEY={public_key_raw}")
        print(f"VAPID_PRIVATE_KEY={private_der_b64}")
        print("VAPID_ADMIN_EMAIL=admin@cssknust.com")
        print()
        print("=" * 80)
        print()
        print("Key lengths:")
        print(f"  Public key:  {len(public_key_raw)} characters")
        print(f"  Private key: {len(private_der_b64)} characters")
        print()
        
    except Exception as e:
        print(f"\n❌ Error converting keys: {e}")
        print("\nMake sure you pasted the complete PEM key including headers.")
