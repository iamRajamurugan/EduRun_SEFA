"""
CLI Interface for Python Docker Compiler
Provides a command-line interface to compile and run Python code using Docker
"""

import argparse
import sys
from pathlib import Path
from compilers.python_compiler_module import PythonDockerCompiler, format_compiler_output

def read_code_from_file(file_path: str) -> str:
    """Read Python code from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)

def interactive_mode(compiler: PythonDockerCompiler):
    """Interactive mode for entering Python code"""
    print("=== Interactive Python Compiler ===")
    print("Enter your Python code (press Ctrl+Z then Enter on Windows, or Ctrl+D on Unix to finish):")
    print()
    
    try:
        lines = []
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break
        
        code = '\n'.join(lines)
        if code.strip():
            print("\n" + "="*50)
            print("COMPILING AND RUNNING CODE...")
            print("="*50)
            
            result = compiler.compile_and_run(code)
            output = format_compiler_output(result)
            print(output)
        else:
            print("No code entered.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Compile and run Python code using Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compiler_cli.py -f script.py              # Compile and run from file
  python compiler_cli.py -f script.py --syntax     # Check syntax only
  python compiler_cli.py --interactive             # Interactive mode
  python compiler_cli.py --image python:3.10       # Use specific Python version
        """
    )
    
    parser.add_argument('-f', '--file', 
                       help='Python file to compile and run')
    
    parser.add_argument('-i', '--interactive', 
                       action='store_true',
                       help='Interactive mode - enter code manually')
    
    parser.add_argument('--syntax', 
                       action='store_true',
                       help='Check syntax only (do not execute)')
    
    parser.add_argument('--image', 
                       default='python:3.9-slim',
                       help='Docker image to use (default: python:3.9-slim)')
    
    parser.add_argument('--timeout', 
                       type=int, 
                       default=30,
                       help='Timeout in seconds (default: 30)')
    
    parser.add_argument('--list-images', 
                       action='store_true',
                       help='List available Python Docker images')
    
    args = parser.parse_args()
    
    # Initialize compiler
    try:
        compiler = PythonDockerCompiler(docker_image=args.image)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Docker is installed and running.")
        sys.exit(1)
    
    # List images and exit
    if args.list_images:
        print("Available Python Docker images:")
        images = compiler.get_available_images()
        if images:
            for img in images:
                print(f"  - {img}")
        else:
            print("  No Python images found locally.")
        sys.exit(0)
    
    # Determine mode
    if args.interactive:
        interactive_mode(compiler)
    elif args.file:
        # File mode
        code = read_code_from_file(args.file)
        print(f"Compiling and running: {args.file}")
        print("="*50)
        
        if args.syntax:
            result = compiler.check_syntax(code)
        else:
            result = compiler.compile_and_run(code, timeout=args.timeout)
        
        output = format_compiler_output(result)
        print(output)
    else:
        print("Error: Must specify either --file or --interactive")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
