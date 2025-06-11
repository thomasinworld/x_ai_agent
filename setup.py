#!/usr/bin/env python3
"""
Easy setup script for Baggy Moonz Twitter Bot
Run this to get everything set up!
"""
import os
import sys
import subprocess
import shutil

def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def setup_env_file():
    """Help user set up the .env file."""
    print("\n🔧 Setting up environment file...")
    
    if os.path.exists(".env"):
        print("⚠️  .env file already exists!")
        choice = input("Do you want to overwrite it? (y/N): ").lower()
        if choice != 'y':
            print("Keeping existing .env file.")
            return True
    
    # Copy example file
    if os.path.exists("env_example.txt"):
        shutil.copy("env_example.txt", ".env")
        print("📄 Created .env file from template")
    else:
        # Create minimal .env file
        with open(".env", "w") as f:
            f.write("# Twitter Login Credentials\n")
            f.write("TWITTER_USERNAME=\n")
            f.write("TWITTER_PASSWORD=\n")
            f.write("\n# OpenAI API Key\n")
            f.write("OPENAI_API_KEY=\n")
        print("📄 Created basic .env file")
    
    print("\n🔐 Now you need to edit the .env file with your credentials:")
    print("1. Your Twitter username or email")
    print("2. Your Twitter password")
    print("3. Your OpenAI API key (get from https://platform.openai.com/api-keys)")
    print("\nEdit the .env file now and then run: python bot.py")
    
    return True

def check_chrome():
    """Check if Chrome is installed."""
    print("\n🌐 Checking for Chrome browser...")
    
    # Common Chrome locations
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome-stable",  # Linux
        "/usr/bin/google-chrome",  # Linux alternative
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"  # Windows 32-bit
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome found!")
            return True
    
    # Try to run chrome command
    try:
        subprocess.run(["google-chrome", "--version"], 
                      capture_output=True, check=True)
        print("✅ Chrome found!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    try:
        subprocess.run(["chrome", "--version"], 
                      capture_output=True, check=True)
        print("✅ Chrome found!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("⚠️  Chrome not found. Please install Google Chrome:")
    print("   - macOS: Download from https://www.google.com/chrome/")
    print("   - Linux: sudo apt install google-chrome-stable")
    print("   - Windows: Download from https://www.google.com/chrome/")
    
    return False

def main():
    print("🚀 Welcome to Baggy Moonz Twitter Bot Setup!")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed. Please fix the package installation issues.")
        return
    
    # Check Chrome
    chrome_ok = check_chrome()
    
    # Setup .env file
    env_ok = setup_env_file()
    
    print("\n" + "=" * 50)
    if chrome_ok and env_ok:
        print("🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Edit the .env file with your credentials")
        print("2. Run: python bot.py")
        print("\nThe bot will open a Chrome window, log in to Twitter, and start posting!")
    else:
        print("⚠️  Setup completed with warnings. Please address the issues above.")

if __name__ == "__main__":
    main() 