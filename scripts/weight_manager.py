#!/usr/bin/env python3
"""
Binary Packer — Encrypt binary at rest, decrypt in memory at runtime.
Usage: python scripts/pack_binary.py <binary_path> <output_path>
"""

import os
import sys
import base64
import hashlib
import struct
from pathlib import Path
from getpass import getpass

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

def derive_key(password, salt=b'binary-pack-v1'):
    """Derive encryption key from password."""
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(key[:32])

def pack_binary(binary_path, output_path, password):
    """Encrypt binary file."""
    if not HAS_CRYPTO:
        print("[ERROR] Install cryptography: pip install cryptography")
        return False
    
    binary_path = Path(binary_path)
    output_path = Path(output_path)
    
    if not binary_path.exists():
        print(f"[ERROR] Binary not found: {binary_path}")
        return False
    
    # Read binary
    with open(binary_path, 'rb') as f:
        binary_data = f.read()
    
    # Create header with metadata
    header = {
        'original_name': binary_path.name,
        'original_size': len(binary_data),
        'packed_at': str(Path.cwd()),
    }
    
    # Encrypt binary
    key = derive_key(password)
    f = Fernet(key)
    encrypted = f.encrypt(binary_data)
    
    # Pack: header_length(4 bytes) + header_json + encrypted_binary
    header_json = str(header).encode()
    header_len = struct.pack('I', len(header_json))
    
    with open(output_path, 'wb') as out:
        out.write(header_len)
        out.write(header_json)
        out.write(encrypted)
    
    # Make executable
    os.chmod(output_path, 0o755)
    
    print(f"[OK] Binary packed: {output_path}")
    print(f"[OK] Original size: {len(binary_data):,} bytes")
    print(f"[OK] Packed size: {output_path.stat().st_size:,} bytes")
    print(f"\nTo run: python scripts/run_packed.py {output_path}")
    return True

def unpack_and_run(packed_path, password):
    """Decrypt and run packed binary in memory."""
    if not HAS_CRYPTO:
        print("[ERROR] Install cryptography: pip install cryptography")
        return None
    
    packed_path = Path(packed_path)
    if not packed_path.exists():
        print(f"[ERROR] Packed file not found: {packed_path}")
        return None
    
    # Read packed file
    with open(packed_path, 'rb') as f:
        header_len = struct.unpack('I', f.read(4))[0]
        header_json = f.read(header_len)
        encrypted = f.read()
    
    # Decrypt
    key = derive_key(password)
    fernet = Fernet(key)
    try:
        binary_data = fernet.decrypt(encrypted)
    except Exception as e:
        print(f"[ERROR] Decryption failed: {e}")
        return None
    
    return binary_data

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Pack:   python scripts/pack_binary.py <binary> <output>")
        print("  Unpack: python scripts/pack_binary.py --unpack <packed> <output>")
        return
    
    if sys.argv[1] == '--unpack':
        # Unpack mode
        packed_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else 'unpacked_binary'
        
        password = getpass("Decryption password: ")
        binary_data = unpack_and_run(packed_path, password)
        
        if binary_data:
            with open(output_path, 'wb') as f:
                f.write(binary_data)
            os.chmod(output_path, 0o755)
            print(f"[OK] Binary unpacked: {output_path}")
    else:
        # Pack mode
        binary_path = sys.argv[1]
        output_path = sys.argv[2]
        
        password = getpass("Encryption password: ")
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("[ERROR] Passwords don't match")
            return
        
        pack_binary(binary_path, output_path, password)

if __name__ == "__main__":
    main()
