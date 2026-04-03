#!/usr/bin/env python3
"""AirOne Professional v4.0 - Setup"""
import sys, subprocess, os

def install():
    deps = ['numpy', 'psutil', 'requests', 'flask', 'pyjwt', 'cryptography', 'pillow']
    print("Installing dependencies...")
    for d in deps:
        subprocess.call([sys.executable, '-m', 'pip', 'install', '-q', d])
    print("Done!")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        install()
    else:
        print("Usage: python setup.py install")
        
if __name__ == '__main__':
    main()