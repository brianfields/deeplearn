#!/usr/bin/env python3
"""
Remove Empty Directories Script

Scans all subdirectories under /backend/modules/ and /mobile/modules/ and removes any empty directories.
Empty directories are those containing no files and no subdirectories.

Usage:
    python scripts/remove_empty_dirs.py --dry-run    # Show what would be removed
    python scripts/remove_empty_dirs.py --force      # Remove empty directories without confirmation
    python scripts/remove_empty_dirs.py              # Interactive mode (default)
    python scripts/remove_empty_dirs.py --target mobile/modules  # Scan specific directory

Options:
    --dry-run: Show what would be removed without actually deleting
    --force: Remove all empty directories without asking for confirmation
    --verbose: Show detailed output of directory scanning
    --target: Scan a specific directory instead of the default modules directories
"""

import argparse
from pathlib import Path
import sys


def is_directory_empty(dir_path: Path) -> bool:
    """Check if a directory is empty (no files, no subdirectories)."""
    try:
        return not any(dir_path.iterdir())
    except PermissionError:
        print(f"⚠️  Permission denied accessing: {dir_path}")
        return False


def find_empty_directories(root_path: Path, verbose: bool = False) -> list[Path]:
    """Find all empty directories under the given root path."""
    empty_dirs = []

    if verbose:
        print(f"🔍 Scanning directories under: {root_path}")

    # Walk through all directories in reverse order (bottom-up)
    # This ensures we check leaf directories first
    for dir_path in sorted(root_path.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if dir_path.is_dir():
            if is_directory_empty(dir_path):
                empty_dirs.append(dir_path)
                if verbose:
                    print(f"📁 Found empty directory: {dir_path}")
            elif verbose:
                # Count items in non-empty directories
                item_count = sum(1 for _ in dir_path.iterdir())
                print(f"📂 Directory contains {item_count} items: {dir_path}")

    return empty_dirs


def remove_empty_directories(empty_dirs: list[Path], dry_run: bool = False, force: bool = False) -> int:
    """Remove the list of empty directories."""
    if not empty_dirs:
        print("✅ No empty directories found.")
        return 0

    print(f"\n📋 Found {len(empty_dirs)} empty directories:")
    for i, dir_path in enumerate(empty_dirs, 1):
        print(f"  {i}. {dir_path}")

    if dry_run:
        print("\n🔍 Dry run mode - no directories will be removed.")
        return 0

    if not force:
        response = input(f"\n❓ Remove {len(empty_dirs)} empty directories? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("❌ Operation cancelled.")
            return 0

    removed_count = 0
    for dir_path in empty_dirs:
        try:
            dir_path.rmdir()
            print(f"🗑️  Removed: {dir_path}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {dir_path}: {e}")

    print(f"\n✅ Successfully removed {removed_count} empty directories.")
    return removed_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove empty directories from the modules folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/remove_empty_dirs.py --dry-run    # Preview what would be removed
  python scripts/remove_empty_dirs.py --force      # Remove without confirmation
  python scripts/remove_empty_dirs.py --verbose    # Show detailed scanning info
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without actually deleting")
    parser.add_argument("--force", action="store_true", help="Remove all empty directories without asking for confirmation")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output during directory scanning")
    parser.add_argument("--target", help="Target directory to scan (defaults to backend/modules and mobile/modules)")

    args = parser.parse_args()

    # Get the target directories to scan
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    project_root = backend_dir.parent

    if args.target:
        # Use specified target directory
        target_path = Path(args.target)
        if not target_path.is_absolute():
            target_path = project_root / args.target

        if not target_path.exists():
            print(f"❌ Error: Target directory not found: {target_path}")
            sys.exit(1)

        target_dirs = [target_path]
    else:
        # Default: scan both backend/modules and mobile/modules
        backend_modules = backend_dir / "modules"
        mobile_modules = project_root / "mobile" / "modules"

        target_dirs = []
        if backend_modules.exists():
            target_dirs.append(backend_modules)
        if mobile_modules.exists():
            target_dirs.append(mobile_modules)

        if not target_dirs:
            print("❌ Error: No modules directories found to scan")
            sys.exit(1)

    print("🧹 Empty Directory Removal Tool")
    all_empty_dirs = []

    for modules_dir in target_dirs:
        print(f"📂 Scanning: {modules_dir}")
        empty_dirs = find_empty_directories(modules_dir, args.verbose)
        all_empty_dirs.extend(empty_dirs)
        print()

    if not all_empty_dirs:
        print("✅ No empty directories found in any scanned location.")
        return

    # Remove empty directories
    removed_count = remove_empty_directories(all_empty_dirs, args.dry_run, args.force)

    if args.dry_run:
        print(f"\n🔍 Dry run complete. Would have removed {len(all_empty_dirs)} directories.")
    else:
        print(f"\n🎉 Operation complete. Removed {removed_count} empty directories.")


if __name__ == "__main__":
    main()
