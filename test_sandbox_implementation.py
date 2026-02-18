#!/usr/bin/env python3
"""
Quick test script to verify sandbox implementation
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported"""
    print("Testing imports...")
    
    try:
        from backend.services.malware_submission_handler import MalwareSubmissionHandler
        print("✅ MalwareSubmissionHandler imported successfully")
    except Exception as e:
        print(f"❌ Failed to import MalwareSubmissionHandler: {e}")
        return False
    
    try:
        from backend.services.analysis_result_processor import AnalysisResultProcessor
        print("✅ AnalysisResultProcessor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import AnalysisResultProcessor: {e}")
        return False
    
    return True

def test_database():
    """Test database schema"""
    print("\nTesting database schema...")
    
    try:
        from backend.database import get_db
        db = get_db()
        
        # Check if new tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['incidents', 'malware_submissions', 'malware_analysis', 'learned_patterns']
        
        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    print("\nTesting directories...")
    
    required_dirs = [
        'backend/services',
        'quarantine/pending',
        'quarantine/analyzed',
        'quarantine/rejected',
        'frontend/sandbox-viewer',
        'docs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory '{dir_path}' exists")
        else:
            print(f"❌ Directory '{dir_path}' missing")
            all_exist = False
    
    return all_exist

def test_files():
    """Test that required files exist"""
    print("\nTesting files...")
    
    required_files = [
        'backend/services/__init__.py',
        'backend/services/malware_submission_handler.py',
        'backend/services/analysis_result_processor.py',
        'frontend/sandbox-viewer/sandbox.html',
        'frontend/sandbox-viewer/sandbox.js',
        'frontend/sandbox-viewer/sandbox.css',
        'docs/SANDBOX_IMPLEMENTATION.md',
        'quarantine/README.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File '{file_path}' exists")
        else:
            print(f"❌ File '{file_path}' missing")
            all_exist = False
    
    return all_exist

def main():
    print("="*60)
    print("SANDBOX FEATURE IMPLEMENTATION TEST")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Database Schema", test_database()))
    results.append(("Directories", test_directories()))
    results.append(("Files", test_files()))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s} : {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Sandbox feature is ready to use.")
        print("\nNext steps:")
        print("1. Start backend: python -m uvicorn backend.main:app --reload --port 8000")
        print("2. Start frontend: cd frontend/sandbox-viewer && python -m http.server 8080")
        print("3. Open browser: http://localhost:8080/sandbox.html")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
