"""
JavaScript Code Compiler Module using Docker
This module provides functionality to run JavaScript code using Docker containers
and capture the runtime messages for display.
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
    """Data class to hold JavaScript execution results"""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    syntax_output: str = ""  # Additional field for JavaScript syntax messages

class JsDockerCompiler:
    """
    A class to run JavaScript code using Docker containers
    """
    
    def __init__(self, docker_image: str = "node:18-slim"):
        """
        Initialize the compiler with a Docker image
        
        Args:
            docker_image (str): Docker image to use for JavaScript execution
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
            logger.info("Docker client initialized successfully for JavaScript")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise ConnectionError("Docker is not running or not accessible")
    
    def _create_temp_file(self, code: str, extension: str = ".js") -> str:
        """
        Create a temporary JavaScript file with the provided code
        
        Args:
            code (str): JavaScript code to write to file
            extension (str): File extension (.js, .mjs, .ts)
            
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
                       js_code: str, 
                       timeout: int = 30,
                       check_syntax_only: bool = False,
                       node_flags: List[str] = None) -> CompilerResult:
        """
        Run JavaScript code in a Docker container
        
        Args:
            js_code (str): JavaScript code to run
            timeout (int): Timeout in seconds for execution
            check_syntax_only (bool): If True, only check syntax without execution
            node_flags (List[str]): Additional Node.js flags
            
        Returns:
            CompilerResult: Object containing execution results
        """
        temp_file = None
        container = None
        
        try:
            # Create temporary file with the code
            temp_file = self._create_temp_file(js_code)
            
            # Default Node.js flags
            if node_flags is None:
                node_flags = ["--no-warnings"]
            
            # Determine the command to run
            if check_syntax_only:
                # Only check syntax, don't run
                command = (
                    f"node {' '.join(node_flags)} --check /app/code.js"
                )
            else:
                # Run the JavaScript code
                command = (
                    f"timeout {timeout}s node {' '.join(node_flags)} /app/code.js"
                )
            
            # Run the container
            start_time = time.time()
            
            container = self.client.containers.run(
                image=self.docker_image,
                command=["bash", "-c", command],
                volumes={temp_file: {'bind': '/app/code.js', 'mode': 'ro'}},
                working_dir='/app',
                detach=True,
                stdout=True,
                stderr=True,
                remove=False  # Don't auto-remove so we can get logs
            )
            
            # Wait for container to finish with timeout
            try:
                result = container.wait(timeout=timeout + 5)  # Extra time for startup
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
                syntax_output = ""
                
                # Try to get separate streams if available
                try:
                    output = container.logs(stdout=True, stderr=False, stream=False).decode('utf-8')
                    error = container.logs(stdout=False, stderr=True, stream=False).decode('utf-8')
                    
                    # For JavaScript, syntax errors appear in stderr
                    if check_syntax_only:
                        syntax_output = error
                        error = error if exit_code != 0 else ""
                    else:
                        # Separate syntax errors from runtime errors
                        if "SyntaxError:" in error or "ReferenceError:" in error:
                            syntax_output = error
                        
                except:
                    # If separate streams fail, use combined logs
                    pass
                    
            except Exception as log_error:
                logger.warning(f"Could not retrieve container logs: {log_error}")
                output = ""
                error = f"Could not retrieve logs: {str(log_error)}"
                syntax_output = ""
            
            success = exit_code == 0
            
            return CompilerResult(
                success=success,
                output=output,
                error=error,
                exit_code=exit_code,
                execution_time=execution_time,
                syntax_output=syntax_output
            )
            
        except Exception as e:
            logger.error(f"Error during JavaScript execution: {e}")
            return CompilerResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0.0,
                syntax_output=""
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
    
    def check_syntax(self, js_code: str) -> CompilerResult:
        """
        Check only the syntax of JavaScript code without execution
        
        Args:
            js_code (str): JavaScript code to check
            
        Returns:
            CompilerResult: Object containing syntax check results
        """
        return self.compile_and_run(js_code, check_syntax_only=True)
    
    def get_available_images(self) -> list:
        """Get list of available JavaScript Docker images"""
        try:
            images = self.client.images.list()
            js_images = [
                img.tags[0] for img in images 
                if img.tags and any('node' in tag or 'javascript' in tag or 'js' in tag for tag in img.tags)
            ]
            return js_images
        except Exception as e:
            logger.error(f"Error getting JavaScript images: {e}")
            return []

def format_js_compiler_output(result: CompilerResult) -> str:
    """
    Format the JavaScript execution result for display
    
    Args:
        result (CompilerResult): The execution result
        
    Returns:
        str: Formatted output string
    """
    output_lines = []
    
    # Header
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    output_lines.append(f"=== JAVASCRIPT EXECUTION RESULT: {status} ===")
    output_lines.append(f"Exit Code: {result.exit_code}")
    output_lines.append(f"Execution Time: {result.execution_time:.2f}s")
    output_lines.append("")
    
    # Syntax Output (syntax errors, warnings)
    if result.syntax_output:
        output_lines.append("🔧 SYNTAX CHECK OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.syntax_output.strip())
        output_lines.append("")
    
    # Program Output (stdout)
    if result.output:
        output_lines.append("📄 PROGRAM OUTPUT:")
        output_lines.append("-" * 40)
        output_lines.append(result.output.strip())
        output_lines.append("")
    
    # Runtime Errors (stderr from program execution)
    if result.error and not result.syntax_output:
        output_lines.append("🚨 RUNTIME ERRORS:")
        output_lines.append("-" * 40)
        output_lines.append(result.error.strip())
        output_lines.append("")
    
    return "\n".join(output_lines)

# Example usage and testing functions
def example_js_usage():
    """Example of how to use the JsDockerCompiler"""
    
    # Sample JavaScript codes to test
    test_codes = [
        # Valid JavaScript code
        """
console.log("Hello, JavaScript World!");

const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((acc, num) => acc + num, 0);

console.log(`Sum of numbers: ${sum}`);

// Modern JavaScript features
const greet = (name) => `Hello, ${name}!`;
console.log(greet("Docker"));

// Async example
setTimeout(() => {
    console.log("Async operation completed!");
}, 100);
        """,
        
        # Code with syntax error
        """
console.log("This has a syntax error");
const missingBrace = {
    name: "test"
    // Missing closing brace
console.log("This won't work");
        """,
        
        # Code with runtime error
        """
console.log("Starting JavaScript execution...");

// This will cause a ReferenceError
console.log(undefinedVariable);

console.log("This line won't be reached");
        """
    ]
    
    try:
        compiler = JsDockerCompiler()
        
        for i, code in enumerate(test_codes, 1):
            print(f"\n{'='*50}")
            print(f"JAVASCRIPT TEST CASE {i}")
            print(f"{'='*50}")
            print(f"Code:\n{code}")
            
            result = compiler.compile_and_run(code)
            formatted_output = format_js_compiler_output(result)
            print(formatted_output)
            
    except Exception as e:
        print(f"Failed to initialize JavaScript compiler: {e}")

if __name__ == "__main__":
    example_js_usage()
