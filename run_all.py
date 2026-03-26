#!/usr/bin/env python3
"""
Run all files in the AI DB Query project.
This script will:
1. Check all Python files for syntax errors
2. Start the Flask application
3. Keep the server running
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error in {file_path}: {e}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def main():
    print("🔍 Checking all Python files for syntax errors...")
    
    # Get all Python files in current directory
    python_files = list(Path('.').glob('*.py'))
    
    syntax_errors = []
    for file_path in python_files:
        print(f"   Checking {file_path.name}...", end=" ")
        is_valid, error = check_syntax(file_path)
        if is_valid:
            print("✅ OK")
        else:
            print("❌ ERROR")
            syntax_errors.append(error)
    
    if syntax_errors:
        print("\n❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"   {error}")
        sys.exit(1)
    
    print("\n✅ All files have valid syntax!")
    print("\n🚀 Starting Flask application...")
    print("   The app will be available at: http://localhost:5000")
    print("   Press Ctrl+C to stop the server\n")
    
    # Run the Flask app
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
