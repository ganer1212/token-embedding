#!/usr/bin/env python3
"""
Memory-Only Executor — Run binary from memory without writing to disk.
Decrypts packed binary and executes directly from memory using memfd_create.
"""

import os
import sys
import ctypes
import ctypes.util
import struct
import base64
import hashlib
import tempfile
from pathlib import Path
from getpass import getpass

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Linux memfd_create syscall number
MEMFD_CREATE_NR = 319  # x86_64
MFD_CLOEXEC = 0x0001

def derive_key(password, salt=b'binary-pack-v1'):
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(key[:32])

def memfd_create(name, flags=0):
    """Create anonymous file in memory."""
    libc = ctypes.CDLL(ctypes.util.find_library('c'))
    syscall = libc.syscall
    syscall.restype = ctypes.c_int
    syscall.argtypes = [ctypes.c_long, ctypes.c_char_p, ctypes.c_uint]
    
    fd = syscall(MEMFD_CREATE_NR, name.encode(), flags)
    if fd < 0:
        raise OSError(f"memfd_create failed: {fd}")
    return fd

def decrypt_packed(packed_path, password):
    """Decrypt packed binary."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography not installed")
    
    with open(packed_path, 'rb') as f:
        header_len = struct.unpack('I', f.read(4))[0]
        header_json = f.read(header_len)
        encrypted = f.read()
    
    key = derive_key(password)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted)

def execute_from_memory(binary_data, args=None):
    """Execute binary directly from memory using memfd_create."""
    if args is None:
        args = []
    
    # Create memory-backed file descriptor
    fd = memfd_create("training_engine", MFD_CLOEXEC)
    
    # Write binary to memory fd
    os.write(fd, binary_data)
    
    # Seek to start
    os.lseek(fd, 0, os.SEEK_SET)
    
    # Create path to memory fd
    fd_path = f"/proc/self/fd/{fd}"
    
    # Fork and exec from memory
    pid = os.fork()
    if pid == 0:
        # Child process
        try:
            # Close all file descriptors except stdin/stdout/stderr and our fd
            for fdesc in range(3, 1024):
                if fdesc != fd:
                    try:
                        os.close(fdesc)
                    except OSError:
                        pass
            
            # Execute from memory
            os.execv(fd_path, [fd_path] + args)
        except Exception as e:
            os._exit(1)
    else:
        # Parent process
        os.close(fd)
        return pid

def execute_fallback(binary_data, args=None):
    """Fallback: write to tmpfs (RAM-backed) and execute."""
    if args is None:
        args = []
    
    # Try /dev/shm first (RAM-backed tmpfs)
    tmp_paths = ['/dev/shm', '/tmp', tempfile.gettempdir()]
    
    for tmp_dir in tmp_paths:
        try:
            tmp_path = Path(tmp_dir) / f".training_{os.getpid()}"
            
            # Write binary
            with open(tmp_path, 'wb') as f:
                f.write(binary_data)
            os.chmod(tmp_path, 0o755)
            
            # Execute
            pid = os.fork()
            if pid == 0:
                try:
                    os.execv(str(tmp_path), [str(tmp_path)] + args)
                except Exception:
                    os._exit(1)
            else:
                # Parent: wait for child then cleanup
                os.waitpid(pid, 0)
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                return pid
        except Exception:
            continue
    
    raise RuntimeError("Failed to execute binary from memory")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory-Only Binary Executor")
    parser.add_argument('packed_binary', help='Path to packed binary (.packed)')
    parser.add_argument('--password', help='Decryption password')
    parser.add_argument('--args', nargs=argparse.REMAINDER, help='Arguments for binary')
    args = parser.parse_args()
    
    packed_path = Path(args.packed_binary)
    if not packed_path.exists():
        print(f"[ERROR] Packed binary not found: {packed_path}")
        sys.exit(1)
    
    password = args.password or getpass("Decryption password: ")
    
    print("[Memory] Decrypting binary...")
    try:
        binary_data = decrypt_packed(packed_path, password)
    except Exception as e:
        print(f"[ERROR] Decryption failed: {e}")
        sys.exit(1)
    
    print(f"[Memory] Binary size: {len(binary_data):,} bytes")
    print("[Memory] Executing from memory...")
    
    try:
        # Try memfd_create first (true memory-only)
        pid = execute_from_memory(binary_data, args.args)
        print(f"[Memory] Process started (PID: {pid})")
        os.waitpid(pid, 0)
    except Exception as e:
        print(f"[Memory] memfd_create failed: {e}")
        print("[Memory] Using tmpfs fallback...")
        try:
            pid = execute_fallback(binary_data, args.args)
            print(f"[Memory] Process completed (PID: {pid})")
        except Exception as e2:
            print(f"[ERROR] Execution failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()
