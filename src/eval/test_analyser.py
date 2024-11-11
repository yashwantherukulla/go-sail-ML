import asyncio
import json
from pathlib import Path
from ..eval.code_analyserv2 import CodeAnalyser
from ..eval.cache_manager import CacheManager
import logging
from dotenv import load_dotenv
import sys

load_dotenv(dotenv_path=".env")

def analyze_with_mode(mode: str, analyser: CodeAnalyser, test_file: Path, test_folder: Path, repo_path: Path):
    """Handle analysis for a specific mode with proper error handling"""
    try:
        # Test file analysis
        print(f"\nAnalyzing file: {test_file}")
        file_result = analyser.analyze_file(str(test_file))
        # Convert model to dict before JSON serialization
        file_result_dict = file_result.model_dump() if hasattr(file_result, 'model_dump') else file_result
        print("File analysis result:")
        print(json.dumps(file_result_dict, indent=2))
        
        # Test folder analysis
        print(f"\nAnalyzing folder: {test_folder}")
        folder_result = analyser.analyze_directory(str(test_folder))
        folder_result_dict = folder_result.model_dump() if hasattr(folder_result, 'model_dump') else folder_result
        print("Folder analysis result:")
        print(json.dumps(folder_result_dict, indent=2))
        
        # Test repo analysis
        print(f"\nAnalyzing repo: {repo_path}")
        repo_result = analyser.analyze_repo(str(repo_path))
        repo_result_dict = repo_result.model_dump() if hasattr(repo_result, 'model_dump') else repo_result
        print("Repo analysis result:")
        print(json.dumps(repo_result_dict, indent=2))
        
        # Test caching
        print("\nTesting cache...")
        cached_result = analyser.analyze_file(str(test_file))
        cached_result_dict = cached_result.model_dump() if hasattr(cached_result, 'model_dump') else cached_result
        print("Cached?", cached_result_dict.get("cached", False))
        
    except Exception as e:
        print(f"Error during {mode} analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_analyser():
    """Main test function with improved error handling and path validation"""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cache manager with absolute path
    cache_dir = Path.cwd() / "analysis_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_manager = CacheManager(str(cache_dir))
    
    # Test paths - convert to absolute paths
    base_path = Path.cwd()
    repo_path = base_path / "cloned_repos" / "regit"
    test_file = repo_path / "main.go" 
    test_folder = repo_path / "cmd"
    
    # Validate paths
    if not all(verify_paths(repo_path, test_file, test_folder)):
        return False
    
    print(f"Using paths:")
    print(f"Repo: {repo_path}")
    print(f"Test file: {test_file}")
    print(f"Test folder: {test_folder}")
    
    # Test all three types of analysis
    analysis_modes = ["code_descriptor", "code_security", "code_quality"]
    success = True
    
    for mode in analysis_modes:
        print(f"\nTesting {mode} analysis...")
        analyser = CodeAnalyser(mode, cache_manager)
        
        mode_success = analyze_with_mode(
            mode, analyser, test_file, test_folder, repo_path
        )
        success = success and mode_success
    
    return success

def verify_paths(repo_path: Path, test_file: Path, test_folder: Path) -> tuple[bool, bool, bool]:
    """Verify all required paths exist"""
    repo_exists = repo_path.exists()
    if not repo_exists:
        print(f"Error: Repository path does not exist: {repo_path}")
    
    file_exists = test_file.exists()
    if not file_exists:
        # Try to find an alternative test file
        py_files = list(repo_path.rglob("*.py"))
        if py_files:
            test_file = py_files[0]
            print(f"Using alternative test file: {test_file}")
            file_exists = True
        else:
            print("Error: No target files found in repository")
    
    folder_exists = test_folder.exists()
    if not folder_exists:
        print(f"Error: Test folder does not exist: {test_folder}")
    
    return repo_exists, file_exists, folder_exists

def verify_environment() -> bool:
    """Verify that all required environment variables exist"""
    import os
    
    required_vars = ["GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    
    return True

if __name__ == "__main__":
    # Verify environment before running
    if verify_environment():
        success = test_analyser()
        sys.exit(0 if success else 1)
    else:
        print("Environment verification failed. Please check the errors above.")
        sys.exit(1)