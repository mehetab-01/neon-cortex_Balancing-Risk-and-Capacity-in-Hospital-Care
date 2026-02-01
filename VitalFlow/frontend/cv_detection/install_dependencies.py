"""
Dependency Installer for CV Detection
Checks and installs required packages for CCTV fall detection
"""
import subprocess
import sys


# Required packages for CV detection
REQUIRED_PACKAGES = [
    "opencv-python",
    "ultralytics",  # YOLOv8
    "numpy",
]


def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    # Handle package name vs import name differences
    import_name = package_name.replace("-", "_").replace("opencv_python", "cv2")
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str) -> bool:
    """Install a package using pip."""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package_name, "-q"
        ])
        return True
    except subprocess.CalledProcessError:
        return False


def check_and_install_dependencies(auto_install: bool = False) -> dict:
    """
    Check for required dependencies and optionally install them.
    
    Args:
        auto_install: If True, automatically install missing packages
        
    Returns:
        Dict with status of each package
    """
    results = {
        "all_installed": True,
        "packages": {}
    }
    
    for package in REQUIRED_PACKAGES:
        is_installed = check_package_installed(package)
        
        if not is_installed:
            results["all_installed"] = False
            
            if auto_install:
                print(f"Installing {package}...")
                success = install_package(package)
                results["packages"][package] = "installed" if success else "failed"
            else:
                results["packages"][package] = "missing"
        else:
            results["packages"][package] = "ok"
    
    return results


def print_installation_instructions():
    """Print manual installation instructions."""
    print("""
    ============================================
    VitalFlow CV Detection - Installation Guide
    ============================================
    
    Required packages:
    
    pip install opencv-python ultralytics numpy
    
    For GPU acceleration (optional):
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    
    The YOLOv8-Pose model will be downloaded automatically on first use.
    ============================================
    """)


if __name__ == "__main__":
    print("Checking dependencies...")
    results = check_and_install_dependencies(auto_install=False)
    
    if results["all_installed"]:
        print("✅ All dependencies installed!")
    else:
        print("❌ Missing dependencies:")
        for pkg, status in results["packages"].items():
            if status != "ok":
                print(f"  - {pkg}: {status}")
        print_installation_instructions()
