#!/usr/bin/env python3
"""
Dependency Checker for Clinical Trial Education Platform Backend

This script verifies that all required dependencies are properly installed
and configured for the application to run successfully.

Run this after installing requirements.txt to ensure everything is set up correctly.
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ ERROR: Python 3.8 or higher is required")
        return False
    return True

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"✗ {package_name} - NOT INSTALLED")
        return False
    else:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package_name} - version {version}")
        except:
            print(f"✓ {package_name} - installed")
        return True

def check_system_command(command):
    """Check if a system command is available"""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ {command} - {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print(f"✗ {command} - NOT FOUND")
    return False

def main():
    print("=" * 60)
    print("Clinical Trial Education Platform - Dependency Check")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check Python version
    print("1. Checking Python version...")
    all_good &= check_python_version()
    print()
    
    # Check core dependencies
    print("2. Checking core Python packages...")
    core_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('sqlalchemy', 'sqlalchemy'),
        ('pydantic', 'pydantic'),
        ('python-dotenv', 'dotenv'),
    ]
    for pkg, import_name in core_packages:
        all_good &= check_package(pkg, import_name)
    print()
    
    # Check AI/ML dependencies
    print("3. Checking AI/ML packages...")
    ai_packages = [
        ('google-generativeai', 'google.generativeai'),
        ('Pillow', 'PIL'),
        ('requests', 'requests'),
    ]
    for pkg, import_name in ai_packages:
        all_good &= check_package(pkg, import_name)
    print()
    
    # Check video generation dependencies
    print("4. Checking video generation packages...")
    video_packages = [
        ('rembg', 'rembg'),
        ('onnxruntime', 'onnxruntime'),
        ('pyttsx3', 'pyttsx3'),
    ]
    for pkg, import_name in video_packages:
        result = check_package(pkg, import_name)
        if not result and pkg == 'pyttsx3':
            print("   ⚠ WARNING: pyttsx3 not installed. TTS will require ELEVENLABS_API_KEY")
        elif not result:
            all_good = False
    print()
    
    # Check system dependencies
    print("5. Checking system dependencies...")
    system_commands = ['ffmpeg']
    for cmd in system_commands:
        result = check_system_command(cmd)
        if not result:
            print(f"   ⚠ WARNING: {cmd} not found. Video generation will fail.")
            print(f"   Install with: brew install {cmd} (macOS) or apt-get install {cmd} (Linux)")
            all_good = False
    print()
    
    # Check optional dependencies
    print("6. Checking optional packages...")
    optional_packages = [
        ('PyPDF2', 'PyPDF2'),
        ('python-jose', 'jose'),
        ('passlib', 'passlib'),
    ]
    for pkg, import_name in optional_packages:
        check_package(pkg, import_name)
    print()
    
    # Summary
    print("=" * 60)
    if all_good:
        print("✓ All critical dependencies are installed!")
        print()
        print("Next steps:")
        print("1. Configure your .env file with API keys")
        print("2. Set up your PostgreSQL database")
        print("3. Run: python main.py")
    else:
        print("✗ Some dependencies are missing or not properly installed")
        print()
        print("To fix:")
        print("1. Run: pip install -r requirements.txt")
        print("2. Install system dependencies (ffmpeg, etc.)")
        print("3. Run this script again to verify")
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
