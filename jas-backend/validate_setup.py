#!/usr/bin/env python
"""
Validation Script for Judgment-to-Action Backend v2.0
Checks all system requirements and dependencies
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_check(status, message):
    symbol = "✅" if status else "❌"
    print(f"{symbol} {message}")

def check_python_version():
    print_header("Python Version")
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 8
    print_check(is_valid, f"Python {version.major}.{version.minor}.{version.micro}")
    return is_valid

def check_packages():
    print_header("Required Packages")
    packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pdfplumber',
        'pytesseract',
        'dotenv'
    ]
    
    all_installed = True
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print_check(True, f"'{package}' installed")
        except ImportError:
            print_check(False, f"'{package}' NOT installed")
            all_installed = False
    
    return all_installed

def check_tesseract():
    print_header("Tesseract OCR")
    try:
        import pytesseract
        try:
            pytesseract.get_tesseract_version()
            print_check(True, "Tesseract found and working")
            return True
        except Exception as e:
            print_check(False, f"Tesseract not found: {str(e)}")
            return False
    except Exception as e:
        print_check(False, f"Could not check Tesseract: {str(e)}")
        return False

def check_directories():
    print_header("Required Directories")
    dirs_to_check = [
        'app',
        'app/services',
        'data',
        'data/documents'
    ]
    
    all_exist = True
    for dir_path in dirs_to_check:
        exists = Path(dir_path).exists()
        print_check(exists, f"Directory '{dir_path}' exists")
        all_exist = all_exist and exists
    
    return all_exist

def check_files():
    print_header("Required Files")
    files_to_check = [
        'app/main.py',
        'app/db.py',
        'app/config.py',
        'app/schemas.py',
        'app/services/ingestion.py',
        'app/services/ocr_service.py',
        'app/services/preprocessing.py',
        'app/services/pipeline.py',
        '.env.example',
        'requirements.txt',
        'API_DOCUMENTATION.md',
        'ARCHITECTURE.md'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        exists = Path(file_path).exists()
        print_check(exists, f"File '{file_path}' exists")
        all_exist = all_exist and exists
    
    return all_exist

def check_imports():
    print_header("Module Imports")
    modules = [
        ('app.config', 'Configuration'),
        ('app.logger', 'Logger'),
        ('app.db', 'Database'),
        ('app.services.ingestion', 'Ingestion Service'),
        ('app.services.ocr_service', 'OCR Service'),
        ('app.services.preprocessing', 'Preprocessing Service'),
        ('app.services.pipeline', 'Pipeline Orchestrator'),
    ]
    
    all_imported = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print_check(True, f"{display_name} module imports")
        except Exception as e:
            print_check(False, f"{display_name} module failed: {str(e)}")
            all_imported = False
    
    return all_imported

def check_fastapi():
    print_header("FastAPI Application")
    try:
        from app.main import app
        routes = len(app.routes)
        print_check(True, f"FastAPI app loads successfully")
        print(f"   Total routes registered: {routes}")
        return True
    except Exception as e:
        print_check(False, f"FastAPI app failed to load: {str(e)}")
        return False

def check_env_file():
    print_header("Environment Configuration")
    env_exists = Path('.env').exists()
    print_check(env_exists, "'.env' file exists")
    
    if env_exists:
        try:
            from app.config import settings
            print_check(True, "Environment settings loaded")
            print(f"   Database: {settings.DATABASE_URL}")
            print(f"   Tesseract: {settings.TESSERACT_CMD}")
            print(f"   Documents dir: {settings.DOCUMENTS_DIR}")
            print(f"   Max upload: {settings.MAX_UPLOAD_SIZE_MB}MB")
        except Exception as e:
            print_check(False, f"Failed to load settings: {str(e)}")
    else:
        print("\n⚠️  Please create .env file from .env.example")
        print("   $ copy .env.example .env")
    
    return env_exists

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  Judgment-to-Action Backend v2.0 Validation".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_packages),
        ("Tesseract OCR", check_tesseract),
        ("Required Directories", check_directories),
        ("Required Files", check_files),
        ("Module Imports", check_imports),
        ("FastAPI Application", check_fastapi),
        ("Environment Configuration", check_env_file),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_check(False, f"Check failed: {str(e)}")
            results[name] = False
    
    print_header("Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}\n")
    
    for check_name, passed in results.items():
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {check_name}")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to run the application.")
        print("\nStart the server with:")
        print("  uvicorn app.main:app --reload")
        print("\nAPI documentation at: http://localhost:8000/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
