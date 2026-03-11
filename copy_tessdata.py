import os
import sys
import ctypes
import shutil

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if is_admin():
    # We are admin, perform the copy
    src = "tam.traineddata"
    dest = r"C:\Program Files\Tesseract-OCR\tessdata\tam.traineddata"
    try:
        shutil.copy2(src, dest)
        print("Successfully copied tam.traineddata")
    except Exception as e:
        print(f"Error copying: {e}")
        
    input("Press Enter to exit...")
else:
    # Re-run the program with admin rights
    print("Requesting administrative privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
