"""Test lifespan with explicit error output."""
import sys
import asyncio
import traceback as tb

# Redirect all output to file
with open('lifespan_test_output.txt', 'w') as f:
    sys.stdout = f
    sys.stderr = f
    
    try:
        print('Step 1: Importing main module...')
        from app.main import app, lifespan
        print('  Imported successfully')
        
        async def test_lifespan():
            print('Step 2: Testing lifespan context manager...')
            async with lifespan(app):
                print('  Lifespan started successfully!')
            print('  Lifespan ended successfully!')
        
        print('Step 3: Running async test...')
        asyncio.run(test_lifespan())
        print('\n=== TEST PASSED ===')
        
    except Exception as e:
        print(f'\n\n=== TEST FAILED ===')
        print(f'Error: {e}')
        print('\nTraceback:')
        tb.print_exc()
        sys.exit(1)
