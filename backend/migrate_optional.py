"""Script to migrate Optional[T] to T | None syntax across the codebase.

This script will:
1. Find all Python files
2. Replace Optional[T] with T | None
3. Remove unused Optional imports
4. Report changes made
"""

import re
from pathlib import Path
from typing import List, Tuple

def migrate_file(filepath: Path) -> Tuple[bool, int]:
    """Migrate a single file from Optional[T] to T | None.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        (was_modified, num_replacements)
    """
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Pattern to match Optional[Something]
    # Handles nested generics like Optional[Dict[str, Any]]
    pattern = r'Optional\[([^\]]+(?:\[[^\]]+\])?[^\]]*)\]'
    
    replacements = 0
    
    # Replace Optional[T] with T | None
    def replace_optional(match):
        nonlocal replacements
        replacements += 1
        inner_type = match.group(1)
        return f'{inner_type} | None'
    
    content = re.sub(pattern, replace_optional, content)
    
    # If we made replacements, check if Optional is still used
    if replacements > 0:
        # Look for remaining uses of Optional
        if not re.search(r'\bOptional\[', content):
            # Remove Optional from typing imports
            # Pattern: from typing import ..., Optional, ...
            content = re.sub(
                r'from typing import ([^;\n]*),\s*Optional\s*,([^;\n]*)',
                r'from typing import \1,\2',
                content
            )
            content = re.sub(
                r'from typing import ([^;\n]*),\s*Optional\s*$',
                r'from typing import \1',
                content,
                flags=re.MULTILINE
            )
            content = re.sub(
                r'from typing import Optional\s*,\s*([^;\n]*)',
                r'from typing import \1',
                content
            )
            # Remove empty commas
            content = re.sub(r'import\s+,', 'import ', content)
            content = re.sub(r',\s*,', ',', content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True, replacements
    
    return False, 0


def migrate_directory(directory: Path, exclude_patterns: List[str] = None) -> None:
    """Migrate all Python files in directory.
    
    Args:
        directory: Root directory to search
        exclude_patterns: Patterns to exclude (e.g., ['venv', '.git'])
    """
    if exclude_patterns is None:
        exclude_patterns = ['venv', '.venv', '__pycache__', '.git', '.pytest_cache']
    
    total_files = 0
    modified_files = 0
    total_replacements = 0
    
    print(f"Searching for Python files in {directory}...")
    
    for pyfile in directory.rglob('*.py'):
        # Skip excluded directories
        if any(pattern in str(pyfile) for pattern in exclude_patterns):
            continue
        
        total_files += 1
        was_modified, replacements = migrate_file(pyfile)
        
        if was_modified:
            modified_files += 1
            total_replacements += replacements
            print(f"✓ {pyfile.relative_to(directory)}: {replacements} replacements")
    
    print("\n" + "="*60)
    print(f"Migration complete!")
    print(f"Files scanned: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"Total replacements: {total_replacements}")
    print("="*60)


if __name__ == "__main__":
    # Migrate the app directory
    app_dir = Path(__file__).parent.parent / "app"
    
    print("Starting Optional[T] → T | None migration...")
    print(f"Target directory: {app_dir}")
    print()
    
    migrate_directory(app_dir)
    
    print("\nMigration complete! Please review changes with git diff.")
