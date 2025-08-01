"""
C++ Code Compiler Module using Docker
This module provides functionality to compile and run C++ code using Docker containers
and capture the compiler/runtime messages for display.
"""

import docker
import tempfile
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CompilerResult:
    """Data class to hold compilation results"""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    compilation_output: str = ""  # Additional field for C++ compilation messages

class CppDockerCompiler:
    """
    A class to compile and run C++ code using Docker containers
    """
    
    def __init__(self, docker_image: str = "gcc:latest"):
        """
        Initialize the compiler with a Docker image
        
        Args:
            docker_image (str): Docker image to use for compilation/execution
        """
        self.docker_image = docker_image
        self.client = None
        self._init_docker_client()
    
    def _init_docker_client(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            # Test if Docker is running
            self.client.ping()
            logger.info("Docker client initialized successfully for C++")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise ConnectionError("Docker is not running or not accessible")
    
    def _create_temp_file(self, code: str, extension: str = ".cpp") -> str:
        """
        Create a temporary C++ file with the provided code
        
        Args:
            code (str): C++ code to write to file
            extension (str): File extension (.cpp, .c, .cc)
            
        Returns:
            str: Path to the temporary file
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
            f.write(code)
            return f.name
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            os.unlink(file_path)
        except OSError:
            pass
    
    def compile_and_run(self, 
                       cpp_code: str, 
                       timeout: int = 30,
                       check_syntax_only: bool = False,
                       compiler_flags: List[str] = None) -> CompilerResult:
        """
        Compile and run C++ code in a Docker container
        
        Args:
            cpp_code (str): C++ code to compile and run
            timeout (int): Timeout in seconds for execution
            check_syntax_only (bool): If True, only check syntax without execution
            compiler_flags (List[str]): Additional compiler flags
            
        Returns:
            CompilerResult: Object containing compilation/execution results
        """
        temp_file = None
        container = None
        
        try:
            # Create temporary file with the code
            temp_file = self._create_temp_file(cpp_code)
            
            # Default compiler flags
            if compiler_flags is None:
                compiler_flags = ["-std=c++17", "-Wall", "-Wextra"]
            
            # Determine the command to run
            if check_syntax_only:
                # Only compile, don't run
                command = (
                    f"g++ {' '.join(compiler_flags)} -fsyntax-only /app/code.cpp"
                )
            else:
                # Compile and run
                command = (
                    f"g++ {' '.join(compiler_flags)} /app/code.cpp -o /app/program && "
                    f"timeout {timeout}s /app/program"
                )
            
            # Run the container
            start_time = time.time()
            
            container = self.client.containers.run(
                image=self.docker_image,
                command=["bash", "-c", command],
                volumes={temp_file: {'bind': '/app/code.cpp', 'mode': 'ro'}},
                working_dir='/app',
                detach=True,
                stdout=True,
                stderr=True,
                remove=False  # Don't auto-remove so we can get logs
            )
            
            # Wait for container to finish with timeout
            try:
                result = container.wait(timeout=timeout + 10)  # Extra time for compilation
                exit_code = result['StatusCode']
            except Exception as e:
                try:
                    container.kill()
                except:
                    pass
                raise TimeoutError(f"Execution timed out after {timeout} seconds")
            
            execution_time = time.time() - start_time
            
            # Get output and error logs
            try:
                logs = container.logs(stdout=True, stderr=True, stream=False).decode('utf-8')
                output = logs
                error = ""
                compilation_output = ""
                
                # Try to get separate streams if available
                try:
                    output = container.logs(stdout=True, stderr=False, stream=False).decode('utf-8')
                    error = container.logs(stdout=False, stderr=True, stream=False).decode('utf-8')
                    
                    # For C++, compilation errors and runtime output can be mixed
                    # If we're just checking syntax, the error stream contains compilation info
                    if check_syntax_only:
                        compilation_output = error
                        error = error if exit_code != 0 else ""
                    else:
                        # Separate compilation errors from runtime errors
                        if "error:" in error or "warning:" in error:
                            compilation_output = error
                        
                except:
                    # If separate streams fail, use combined logs
                    pass
                    
            except Exception as log_error:
                logger.warning(f"Could not retrieve container logs: {log_error}")
                output = ""
                error = f"Could not retrieve logs: {str(log_error)}"
                compilation_output = ""
            
            success = exit_code == 0
            
            return CompilerResult(
                success=success,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time=execution_time,
                compilation_output=compilation_output
            )
            
        except Exception as e:
            logger.error(f"Error during C++ compilation/execution: {e}")
            return CompilerResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0.0,
                compilation_output=""
            )
        
        finally:
            # Cleanup
            if temp_file:
                self._cleanup_temp_file(temp_file)
            
            # Remove container if it exists
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def check_syntax(self, cpp_code: str) -> CompilerResult:
        """
        Check only the syntax of C++ code without execution
        
        Args:
            cpp_code (str): C++ code to check
            
        Returns:
            CompilerResult: Object containing syntax check results
        """
        return self.compile_and_run(cpp_code, check_syntax_only=True)
    
    def get_available_images(self) -> list:
        """Get list of available C++ Docker images"""
        try:
            images = self.client.images.list()
            cpp_images = [
                img.tags[0] for img in images 
                if img.tags and any('gcc' in tag or 'clang' in tag or 'cpp' in tag for tag in img.tags)
            ]
            return cpp_images
        except Exception as e:
            logger.error(f"Error getting C++ images: {e}")
            return []

def format_cpp_compiler_output(result: CompilerResult) -> str:
    """
    Format the C++ compiler result for display
    
    Args:
        result (CompilerResult): The compilation result
        
    Returns:
        str: Formatted output string
    """
    output_lines = []
    
    # Header
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    output_lines.append(f"=== C++ COMPILATION RESULT: {status} ===")
    output_lines.append(f"Exit Code: {result.exit_code}")
    output_lines.append(f"Execution Time: {result.execution_time:.2f}s")
    output_lines.append("")
    
    # Compilation Output (warnings, errors)
    if result.compilation_output:
        output_lines.append("🔧 COMPILATION OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.compilation_output.strip())
        output_lines.append("")
    
    # Program Output (stdout)
    if result.output:
        output_lines.append("📄 PROGRAM OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.output.strip())
        output_lines.append("")
    
    # Runtime Errors (stderr from program execution)
    if result.error and not result.compilation_output:
        output_lines.append("🚨 RUNTIME ERRORS:")
        output_lines.append("-" * 40)
        output_lines.append(result.error.strip())
        output_lines.append("")
    
    return "\n".join(output_lines)

# Example usage and testing functions
def example_cpp_usage():
    """Example of how to use the CppDockerCompiler"""
    
    # Sample C++ codes to test
    test_codes = [
        # Valid C++ code
        """
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::cout << "Hello, C++ World!" << std::endl;
    
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = 0;
    
    for (int num : numbers) {
        sum += num;
    }
    
    std::cout << "Sum of numbers: " << sum << std::endl;
    
    return 0;
}
        """,
        
        # Code with syntax error
        """
#include <iostream>

int main() {
    std::cout << "This has a syntax error" << std::endl
    // Missing semicolon above
    return 0;
}
        """,
        
        # Code with runtime error
        """
#include <iostream>
#include <vector>

int main() {
    std::vector<int> vec = {1, 2, 3};
    std::cout << "Accessing element at index 10: " << vec.at(10) << std::endl;
    return 0;
}
        """
    ]
    
    try:
        compiler = CppDockerCompiler()
        
        for i, code in enumerate(test_codes, 1):
            print(f"\n{'='*50}")
            print(f"C++ TEST CASE {i}")
            print(f"{'='*50}")
            print(f"Code:\n{code}")
            
            result = compiler.compile_and_run(code)
            formatted_output = format_cpp_compiler_output(result)
            print(formatted_output)
            
    except Exception as e:
        print(f"Failed to initialize C++ compiler: {e}")

if __name__ == "__main__":
    example_cpp_usage()
