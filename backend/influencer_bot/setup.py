#!/usr/bin/env python3
# ============================================
# Setup Helper - Python-based setup
# ============================================

import os
import sys
import subprocess
import platform

def print_banner():
    """Print setup banner"""
    print("\n")
    print("╔" + "="*60 + "╗")
    print("║" + " "*12 + "🎯 INFLUENCER FINDER BOT - SETUP 🎯" + " "*11 + "║")
    print("║" + " "*60 + "║")
    print("║" + " Installing & Verifying Dependencies".ljust(60) + "║")
    print("╚" + "="*60 + "╝")
    print("\n")

def run_command(cmd, description):
    """Run a command and handle errors"""
    try:
        print(f"📦 {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"⚠️  {description} (non-zero exit)")
            if result.stderr:
                print(f"   Error: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def main():
    """Main setup function"""
    print_banner()
    
    os_type = platform.system()
    print(f"System: {os_type}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    # Step 1: System dependencies (if Linux)
    if os_type == "Linux":
        print("="*60)
        print("Step 1: Installing System Dependencies")
        print("="*60 + "\n")
        
        deps_installed = run_command(
            "sudo playwright install-deps 2>/dev/null || sudo apt-get update && sudo apt-get install -y libasound2",
            "Installing Playwright system dependencies"
        )
        
        if not deps_installed:
            print("\n⚠️  Some system dependencies might be missing")
            print("   If you see Playwright errors, run: sudo playwright install-deps\n")
    
    # Step 2: Create/Verify venv
    print("\n" + "="*60)
    print("Step 2: Virtual Environment")
    print("="*60 + "\n")
    
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment...")
        run_command(f"python3 -m venv {venv_dir}", "Creating venv")
    else:
        print(f"✅ Virtual environment exists")
    
    # Detect pip command
    if os.name == 'nt':  # Windows
        pip_cmd = f"{venv_dir}\\Scripts\\pip"
        activate_cmd = f"{venv_dir}\\Scripts\\activate"
    else:  # Unix-like
        pip_cmd = f"{venv_dir}/bin/pip"
        activate_cmd = f"source {venv_dir}/bin/activate"
    
    # Step 3: Install packages
    print("\n" + "="*60)
    print("Step 3: Installing Python Packages")
    print("="*60 + "\n")
    
    # Upgrade pip
    run_command(f"{pip_cmd} install --upgrade pip setuptools wheel -q", "Upgrading pip")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements")
    else:
        print("❌ requirements.txt not found")
        return False
    
    # Step 4: Install Playwright browsers
    print("\n" + "="*60)
    print("Step 4: Installing Playwright Browsers")
    print("="*60 + "\n")
    
    if os.name == 'nt':  # Windows
        playwright_cmd = f"{venv_dir}\\Scripts\\playwright install chromium"
    else:  # Unix-like
        playwright_cmd = f"{venv_dir}/bin/playwright install chromium"
    
    run_command(playwright_cmd, "Installing Playwright browsers")
    
    # Step 5: Verify installation
    print("\n" + "="*60)
    print("Step 5: Verification")
    print("="*60 + "\n")
    
    try:
        import playwright
        import pandas
        import bs4
        print("✅ All Python packages verified")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False
    
    # Print completion message
    print("\n")
    print("╔" + "="*60 + "╗")
    print("║" + " "*20 + "✅ SETUP COMPLETE! 🎉" + " "*19 + "║")
    print("║" + " "*60 + "║")
    print("║" + " Next steps:".ljust(60) + "║")
    
    if os.name == 'nt':
        print("║" + f" 1. {venv_dir}\\Scripts\\activate".ljust(60) + "║")
    else:
        print("║" + f" 1. source {venv_dir}/bin/activate".ljust(60) + "║")
    
    print("║" + " 2. python3 run.py".ljust(60) + "║")
    print("║" + " "*60 + "║")
    print("╚" + "="*60 + "╝")
    print("\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
