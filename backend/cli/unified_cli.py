#!/usr/bin/env python3
"""
Unified CLI for Python, C++ and JavaScript Docker Compiler
"""

import argparse
import sys
from compilers.python_compiler_module import PythonDockerCompiler, format_compiler_output
from compilers.cpp_compiler_module import CppDockerCompiler, format_cpp_compiler_output
from compilers.js_compiler_module import JsDockerCompiler, format_js_compiler_output

def detect_language(code):
    """Auto-detect programming language"""
    code_lower = code.lower().strip()
    
    # C++ indicators
    cpp_indicators = [
        '#include <iostream>', '#include<iostream>', 'std::cout', 'std::cin', 
        'std::endl', 'int main()', 'int main(', 'using namespace std',
        '#include <vector>', '#include <string>', 'cout <<', 'cin >>'
    ]
    
    # JavaScript indicators
    js_indicators = [
        'console.log(', 'console.error(', 'function(', 'const ', 'let ', 'var ',
        '=>', 'require(', 'module.exports', 'document.', 'window.', 'alert(',
        'settimeout(', 'setinterval('
    ]
    
    # Python indicators  
    python_indicators = [
        'print(', 'import ', 'from ', 'def ', 'if __name__ == "__main__"',
        'input(', 'len(', 'range(', 'str(', 'int(', 'float('
    ]
    
    cpp_score = sum(1 for indicator in cpp_indicators if indicator in code_lower)
    js_score = sum(1 for indicator in js_indicators if indicator in code_lower)
    python_score = sum(1 for indicator in python_indicators if indicator in code_lower)
    
    # Additional pattern checks
    if cpp_score == 0 and js_score == 0 and python_score == 0:
        if '{' in code and '}' in code and ';' in code:
            # Could be C++ or JavaScript
            if 'main(' in code_lower:
                cpp_score += 2
            else:
                js_score += 1
        if ':' in code and not ';' in code:
            python_score += 1
    
    # Return the language with highest score
    scores = {'cpp': cpp_score, 'js': js_score, 'python': python_score}
    return max(scores, key=scores.get)

def main():
    parser = argparse.ArgumentParser(description='Unified Docker Compiler for Python, C++ and JavaScript')
    
    # Mode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='File containing code to compile')
    group.add_argument('-c', '--code', type=str, help='Code string to compile')
    group.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    
    # Options
    parser.add_argument('-l', '--language', choices=['python', 'cpp', 'js', 'auto'], 
                        default='auto', help='Programming language (default: auto-detect)')
    parser.add_argument('-s', '--syntax-only', action='store_true', 
                        help='Check syntax only')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                        help='Execution timeout in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Get code
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            print(f"📁 Loaded code from: {args.file}")
        except FileNotFoundError:
            print(f"❌ Error: File '{args.file}' not found")
            return 1
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return 1
    elif args.code:
        code = args.code
    else:  # Interactive mode
        print("🔧 Unified Docker Compiler - Interactive Mode")
        print("Enter your Python, C++ or JavaScript code (press Ctrl+D or type 'END' on a new line to finish):")
        print("-" * 60)
        
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
        except EOFError:
            pass
        
        code = '\n'.join(lines)
        if not code.strip():
            print("❌ No code provided")
            return 1
    
    # Detect language
    if args.language == 'auto':
        language = detect_language(code)
        print(f"🔍 Auto-detected language: {language.upper()}")
    else:
        language = args.language
        print(f"🎯 Using specified language: {language.upper()}")
    
    # Initialize compiler
    try:
        if language == 'cpp':
            compiler = CppDockerCompiler()
            format_func = format_cpp_compiler_output
        elif language == 'js':
            compiler = JsDockerCompiler()
            format_func = format_js_compiler_output
        else:
            compiler = PythonDockerCompiler()
            format_func = format_compiler_output
        
        print(f"✅ {language.upper()} compiler initialized")
    except Exception as e:
        print(f"❌ Failed to initialize {language.upper()} compiler: {e}")
        return 1
    
    # Compile and run
    print(f"🚀 {'Checking syntax' if args.syntax_only else 'Compiling and running'}...")
    print("-" * 60)
    
    try:
        if args.syntax_only:
            result = compiler.check_syntax(code)
        else:
            result = compiler.compile_and_run(code, timeout=args.timeout)
        
        # Display results
        print(format_func(result))
        
        return 0 if result.success else 1
        
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
