"""Simple wrapper to capture full traceback."""
import sys
import traceback

try:
    exec(open('execute_pipeline_test.py', encoding='utf-8').read())
except Exception as e:
    with open('error_log.txt', 'w') as f:
        f.write("Error occurred:\n")
        f.write(str(e) + "\n\n")
        f.write("Full traceback:\n")
        traceback.print_exc(file=f)
    
    print(f"Error: {e}")
    print("Full traceback saved to error_log.txt")
    with open('error_log.txt', 'r') as f:
        print(f.read())
    sys.exit(1)
