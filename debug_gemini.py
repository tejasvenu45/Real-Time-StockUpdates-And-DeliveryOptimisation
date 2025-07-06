#!/usr/bin/env python3
"""
Script to load .env file and run the fulfillment tests
"""

import os
import sys
import subprocess
from pathlib import Path

def load_env_file():
    """Load .env file manually"""
    print("🔧 Loading .env file...")
    
    # Find .env file
    env_paths = [
        Path('.env'),
        Path('../.env'),
        Path('../../.env'),
        Path('./.env'),
    ]
    
    env_file = None
    for path in env_paths:
        if path.exists():
            env_file = path
            break
    
    if not env_file:
        print("❌ .env file not found!")
        print("Checked locations:")
        for path in env_paths:
            print(f"  - {path.absolute()}")
        return False
    
    print(f"✅ Found .env file: {env_file.absolute()}")
    
    # Read .env file
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        print("📄 .env file contents:")
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    # Set environment variable
                    os.environ[key] = value
                    
                    # Show (but mask sensitive values)
                    if 'API_KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                        display_value = f"{value[:10]}..." if len(value) > 10 else "***"
                        print(f"  {key}={display_value}")
                    else:
                        print(f"  {key}={value}")
        
        # Check if GEMINI_API_KEY was loaded
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            print(f"✅ GEMINI_API_KEY loaded successfully (length: {len(gemini_key)})")
            return True
        else:
            print("❌ GEMINI_API_KEY not found in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def install_dotenv_if_needed():
    """Install python-dotenv if not available"""
    try:
        import dotenv
        return True
    except ImportError:
        print("📦 Installing python-dotenv...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
            print("✅ python-dotenv installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install python-dotenv: {e}")
            return False

def load_env_with_dotenv():
    """Load .env using python-dotenv"""
    if not install_dotenv_if_needed():
        return False
    
    try:
        from dotenv import load_dotenv
        
        # Try to load .env from current and parent directories
        env_paths = [
            Path('.env'),
            Path('../.env'), 
            Path('../../.env'),
        ]
        
        loaded = False
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded .env file using python-dotenv: {env_path.absolute()}")
                loaded = True
                break
        
        if not loaded:
            # Try default load_dotenv (searches automatically)
            load_dotenv()
            print("✅ Loaded .env file using python-dotenv (auto-search)")
        
        # Check if it worked
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            print(f"✅ GEMINI_API_KEY loaded (length: {len(gemini_key)})")
            return True
        else:
            print("❌ GEMINI_API_KEY still not available after loading .env")
            return False
            
    except Exception as e:
        print(f"❌ Error loading .env with python-dotenv: {e}")
        return False

def run_tests():
    """Run the fulfillment tests"""
    print("\n🧪 Running fulfillment tests...")
    try:
        result = subprocess.run([sys.executable, 'test_ai.py'], 
                              capture_output=False, 
                              text=True,
                              cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main function"""
    print("🚀 .env Loader and Test Runner")
    print("=" * 50)
    
    # Method 1: Try python-dotenv first (cleaner)
    print("\n📦 Method 1: Using python-dotenv...")
    if load_env_with_dotenv():
        print("✅ .env loaded successfully with python-dotenv")
    else:
        print("⚠️ python-dotenv method failed, trying manual method...")
        
        # Method 2: Manual parsing
        print("\n🔧 Method 2: Manual .env parsing...")
        if load_env_file():
            print("✅ .env loaded successfully manually")
        else:
            print("❌ Failed to load .env file")
            print("\n💡 TROUBLESHOOTING:")
            print("1. Make sure .env file exists in your project root")
            print("2. Check .env file format: GEMINI_API_KEY=your_key_here")
            print("3. No spaces around the = sign")
            print("4. No quotes needed around the value")
            return
    
    # Verify environment variable is now set
    print(f"\n🔍 Final check - GEMINI_API_KEY: {'✅ SET' if os.getenv('GEMINI_API_KEY') else '❌ NOT SET'}")
    
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ Cannot proceed - GEMINI_API_KEY still not available")
        return
    
    # Run tests
    print("\n" + "=" * 50)
    if run_tests():
        print("✅ Tests completed successfully!")
    else:
        print("⚠️ Tests completed with some issues")

if __name__ == "__main__":
    main()