"""
Python Code Compiler Module using Docker
This module provides functionality to compile and run Python code using Docker containers
and capture the compiler/runtime messages for display.
"""

import docker
import tempfile
import os
import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
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

class PythonDockerCompiler:
    """
    A class to compile and run Python code using Docker containers
    """
    
    def __init__(self, docker_image: str = "python:3.9-slim"):
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
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise ConnectionError("Docker is not running or not accessible")
    
    def _create_temp_file(self, code: str) -> str:
        """
        Create a temporary Python file with the provided code
        
        Args:
            code (str): Python code to write to file
            
        Returns:
            str: Path to the temporary file
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            return f.name
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            os.unlink(file_path)
        except OSError:
            pass
    
    def compile_and_run(self, 
                       python_code: str, 
                       timeout: int = 30,
                       check_syntax_only: bool = False) -> CompilerResult:
        """
        Compile and run Python code in a Docker container
        
        Args:
            python_code (str): Python code to compile and run
            timeout (int): Timeout in seconds for execution
            check_syntax_only (bool): If True, only check syntax without execution
            
        Returns:
            CompilerResult: Object containing compilation/execution results
        """
        temp_file = None
        container = None
        
        try:
            # Create temporary file with the code
            temp_file = self._create_temp_file(python_code)
            
            # Determine the command to run
            if check_syntax_only:
                command = f"python -m py_compile /app/code.py"
            else:
                command = f"python /app/code.py"
            
            # Run the container
            import time
            start_time = time.time()
            
            container = self.client.containers.run(
                image=self.docker_image,
                command=command,
                volumes={temp_file: {'bind': '/app/code.py', 'mode': 'ro'}},
                working_dir='/app',
                detach=True,
                stdout=True,
                stderr=True,
                remove=False  # Don't auto-remove so we can get logs
            )
            
            # Wait for container to finish with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result['StatusCode']
            except Exception as e:
                try:
                    container.kill()
                except:
                    pass
                raise TimeoutError(f"Execution timed out after {timeout} seconds")
            
            execution_time = time.time() - start_time
            
            # Get output and error logs (get them before container is removed)
            try:
                logs = container.logs(stdout=True, stderr=True, stream=False).decode('utf-8')
                # Split logs into stdout and stderr if possible
                output = logs
                error = ""
                
                # Try to get separate streams if available
                try:
                    output = container.logs(stdout=True, stderr=False, stream=False).decode('utf-8')
                    error = container.logs(stdout=False, stderr=True, stream=False).decode('utf-8')
                except:
                    # If separate streams fail, use combined logs
                    pass
            except Exception as log_error:
                logger.warning(f"Could not retrieve container logs: {log_error}")
                output = ""
                error = f"Could not retrieve logs: {str(log_error)}"
            
            success = exit_code == 0
            
            return CompilerResult(
                success=success,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error during compilation/execution: {e}")
            return CompilerResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0.0
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
    
    def check_syntax(self, python_code: str) -> CompilerResult:
        """
        Check only the syntax of Python code without execution
        
        Args:
            python_code (str): Python code to check
            
        Returns:
            CompilerResult: Object containing syntax check results
        """
        return self.compile_and_run(python_code, check_syntax_only=True)
    
    def get_available_images(self) -> list:
        """Get list of available Python Docker images"""
        try:
            images = self.client.images.list()
            python_images = [
                img.tags[0] for img in images 
                if img.tags and any('python' in tag for tag in img.tags)
            ]
            return python_images
        except Exception as e:
            logger.error(f"Error getting images: {e}")
            return []

def format_compiler_output(result: CompilerResult) -> str:
    """
    Format the compiler result for display
    
    Args:
        result (CompilerResult): The compilation result
        
    Returns:
        str: Formatted output string
    """
    output_lines = []
    
    # Header
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    output_lines.append(f"=== COMPILATION RESULT: {status} ===")
    output_lines.append(f"Exit Code: {result.exit_code}")
    output_lines.append(f"Execution Time: {result.execution_time:.2f}s")
    output_lines.append("")
    
    # Standard Output
    if result.output:
        output_lines.append("📄 STANDARD OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.output.strip())
        output_lines.append("")
    
    # Error Output
    if result.error:
        output_lines.append("🚨 ERROR OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.error.strip())
        output_lines.append("")
    
    return "\n".join(output_lines)

# Example usage and testing functions
def example_usage():
    """Example of how to use the PythonDockerCompiler"""
    
    # Sample Python code to test
    test_codes = [
        # Valid code
        """
print("Hello, World!")
print("Python version check:")
import sys
print(f"Python {sys.version}")
        """,
        
        # Code with syntax error
        """
print("This has a syntax error"
print("Missing closing parenthesis")
        """,
        
        # Code with runtime error
        """
print("This will cause a runtime error:")
x = 1 / 0
        """
    ]
    
    try:
        compiler = PythonDockerCompiler()
        
        for i, code in enumerate(test_codes, 1):
            print(f"\n{'='*50}")
            print(f"TEST CASE {i}")
            print(f"{'='*50}")
            print(f"Code:\n{code}")
            
            result = compiler.compile_and_run(code)
            formatted_output = format_compiler_output(result)
            print(formatted_output)
            
    except Exception as e:
        print(f"Failed to initialize compiler: {e}")

if __name__ == "__main__":
    example_usage()
