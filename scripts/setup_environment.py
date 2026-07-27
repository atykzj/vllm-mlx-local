#!/usr/bin/env python3
"""Environment setup and validation script.

This script checks if the environment is properly configured for vLLM-MLX:
- Python version
- Required dependencies
- Memory availability
- System compatibility
"""

import sys
import subprocess
import platform
from pathlib import Path


# Constants
MINIMUM_PYTHON_VERSION = (3, 11)
REQUIRED_PACKAGES = [
    "mlx",
    "mlx_lm",
    "psutil",
    "fastapi",
    "uvicorn",
    "pydantic",
    "pytest",
]
MINIMUM_MEMORY_GB = 8


def print_section(title: str):
    """Print a section header.
    
    Args:
        title: Section title to display
    """
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)


def check_python_version() -> bool:
    """Check if Python version meets requirements.
    
    Returns:
        True if version is sufficient, False otherwise
    """
    current_version = sys.version_info[:2]
    
    if current_version >= MINIMUM_PYTHON_VERSION:
        print(f"✅ Python {current_version[0]}.{current_version[1]} (required: {MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]}+)")
        return True
    else:
        print(f"❌ Python {current_version[0]}.{current_version[1]} (required: {MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]}+)")
        return False


def check_macos() -> bool:
    """Check if running on macOS with Apple Silicon.
    
    Returns:
        True if on compatible macOS, False otherwise
    """
    if platform.system() != "Darwin":
        print("❌ Not running on macOS")
        return False
    
    # Check for Apple Silicon
    machine = platform.machine()
    if machine != "arm64":
        print(f"⚠️  Running on {machine} (Apple Silicon recommended)")
        return True
    
    print(f"✅ macOS with Apple Silicon ({machine})")
    return True


def check_package(package_name: str) -> bool:
    """Check if a Python package is installed.
    
    Args:
        package_name: Name of package to check
        
    Returns:
        True if package is installed, False otherwise
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_dependencies() -> bool:
    """Check if all required packages are installed.
    
    Returns:
        True if all packages are installed, False otherwise
    """
    all_installed = True
    
    for package in REQUIRED_PACKAGES:
        if check_package(package):
            print(f"✅ {package}")
        else:
            print(f"❌ {package} (not installed)")
            all_installed = False
    
    return all_installed


def check_memory() -> bool:
    """Check if sufficient memory is available.
    
    Returns:
        True if memory is sufficient, False otherwise
    """
    try:
        import psutil
        
        # Get available memory
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        
        print(f"Total Memory:     {total_gb:.1f} GB")
        print(f"Available Memory: {available_gb:.1f} GB")
        
        if available_gb >= MINIMUM_MEMORY_GB:
            print(f"✅ Sufficient memory (required: {MINIMUM_MEMORY_GB}GB+)")
            return True
        else:
            print(f"⚠️  Low memory (recommended: {MINIMUM_MEMORY_GB}GB+)")
            return False
            
    except ImportError:
        print("⚠️  Cannot check memory (psutil not installed)")
        return False


def check_project_structure() -> bool:
    """Check if project structure is correct.
    
    Returns:
        True if structure is valid, False otherwise
    """
    required_paths = [
        "src/vllm_mlx/__init__.py",
        "src/vllm_mlx/server.py",
        "src/vllm_mlx/engine.py",
        "src/vllm_mlx/memory.py",
        "src/vllm_mlx/models.py",
        "requirements.txt",
    ]
    
    # Get project root (parent of scripts folder)
    project_root = Path(__file__).parent.parent
    all_exist = True
    
    for path_str in required_paths:
        path = project_root / path_str
        if path.exists():
            print(f"✅ {path_str}")
        else:
            print(f"❌ {path_str} (not found)")
            all_exist = False
    
    return all_exist


def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("\nAttempting to install dependencies...")
    
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Install dependencies
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file)
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as error:
        print(f"❌ Failed to install dependencies: {error}")
        return False


def get_recommended_model():
    """Get recommended model based on available memory."""
    try:
        # Import after checking dependencies
        from vllm_mlx.memory import get_memory_info
        from vllm_mlx.models import recommend_model
        
        memInfo = get_memory_info()
        recommendation = recommend_model(memInfo["available_gb"])
        
        print(f"\nRecommended Model: {recommendation['model_id']}")
        print(f"  Model Weights:  {recommendation['weights_gb']:.1f} GB")
        print(f"  KV Cache:       {recommendation['kv_cache_gb']:.1f} GB")
        
    except Exception as error:
        print(f"⚠️  Could not determine recommended model: {error}")


def main():
    """Main setup validation function."""
    print("vLLM-MLX Local - Environment Setup")
    
    # Track overall status
    all_checks_passed = True
    
    # Check Python version
    print_section("Python Version")
    if not check_python_version():
        all_checks_passed = False
    
    # Check macOS compatibility
    print_section("System Compatibility")
    if not check_macos():
        all_checks_passed = False
    
    # Check project structure
    print_section("Project Structure")
    if not check_project_structure():
        all_checks_passed = False
        print("\n⚠️  Project structure incomplete. Are you in the project root?")
    
    # Check dependencies
    print_section("Dependencies")
    dependencies_ok = check_dependencies()
    
    if not dependencies_ok:
        print("\n❌ Some dependencies are missing.")
        response = input("Would you like to install them now? (y/n): ")
        
        if response.lower() == 'y':
            if install_dependencies():
                dependencies_ok = True
            else:
                all_checks_passed = False
        else:
            all_checks_passed = False
            print("\nTo install manually, run:")
            print("  pip install -r requirements.txt")
    
    # Check memory
    print_section("Memory")
    if not check_memory():
        all_checks_passed = False
    
    # Get recommended model
    if dependencies_ok:
        print_section("Model Recommendation")
        get_recommended_model()
    
    # Final summary
    print_section("Setup Summary")
    
    if all_checks_passed:
        print("✅ Environment is ready!")
        print("\nNext steps:")
        print("  1. Start the server:")
        print("     python -m vllm_mlx.server")
        print("\n  2. Test the API:")
        print("     python scripts/test_single_request.py")
        print("\n  3. Test concurrent requests:")
        print("     python scripts/test_concurrent_requests.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
