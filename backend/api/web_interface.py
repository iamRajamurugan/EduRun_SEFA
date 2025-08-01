"""
Unified Web Interface for Python, C++ and JavaScript Docker Compiler
Provides both API endpoints and serves the React frontend
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.compilers.python_compiler_module import PythonDockerCompiler, format_compiler_output, CompilerResult as PythonCompilerResult
from backend.compilers.cpp_compiler_module import CppDockerCompiler, format_cpp_compiler_output, CompilerResult as CppCompilerResult
from backend.compilers.js_compiler_module import JsDockerCompiler, format_js_compiler_output, CompilerResult as JsCompilerResult
import json
import logging
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Enable CORS for frontend integration (production URLs)
CORS(app, origins=[
    "http://localhost:5173", 
    "http://localhost:3000", 
    "http://localhost:4000",
    "http://localhost:8080",
    "https://*.railway.app",  # Railway production URLs
    "https://*.vercel.app"    # If frontend deployed separately
])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global compiler instances
python_compiler = None
cpp_compiler = None
js_compiler = None

# Path to the React frontend build
# Frontend configuration
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'edurun-ai-code-buddy-76', 'dist')

def init_compilers():
    """Initialize Python, C++ and JavaScript Docker compilers"""
    global python_compiler, cpp_compiler, js_compiler
    
    success = True
    
    try:
        python_compiler = PythonDockerCompiler()
        logger.info("Python Docker compiler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Python compiler: {e}")
        python_compiler = None
        success = False
    
    try:
        cpp_compiler = CppDockerCompiler()
        logger.info("C++ Docker compiler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize C++ compiler: {e}")
        cpp_compiler = None
        success = False
    
    try:
        js_compiler = JsDockerCompiler()
        logger.info("JavaScript Docker compiler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize JavaScript compiler: {e}")
        js_compiler = None
        success = False
    
    return success

def detect_language(code):
    """Detect programming language based on code content"""
    code_lower = code.lower().strip()
    
    # C++ indicators
    cpp_indicators = [
        '#include <iostream>',
        '#include<iostream>',
        'std::cout',
        'std::cin',
        'std::endl',
        'int main()',
        'int main(',
        'using namespace std',
        '#include <vector>',
        '#include <string>',
        'cout <<',
        'cin >>'
    ]
    
    # JavaScript indicators
    js_indicators = [
        'console.log(',
        'console.error(',
        'function(',
        'const ',
        'let ',
        'var ',
        '=>',
        'require(',
        'module.exports',
        'document.',
        'window.',
        'alert(',
        'settimeout(',
        'setinterval('
    ]
    
    # Python indicators  
    python_indicators = [
        'print(',
        'import ',
        'from ',
        'def ',
        'if __name__ == "__main__"',
        'input(',
        'len(',
        'range(',
        'str(',
        'int(',
        'float('
    ]
    
    cpp_score = sum(1 for indicator in cpp_indicators if indicator in code_lower)
    js_score = sum(1 for indicator in js_indicators if indicator in code_lower)
    python_score = sum(1 for indicator in python_indicators if indicator in code_lower)
    
    # If no clear indicators, check for typical syntax patterns
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

@app.route('/')
def index():
    """Serve React frontend or fallback to simple interface"""
    if os.path.exists(FRONTEND_PATH):
        return send_from_directory(FRONTEND_PATH, 'index.html')
    else:
        # Fallback to simple interface if React build doesn't exist
        return render_template('unified_index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend static files"""
    if os.path.exists(FRONTEND_PATH):
        if os.path.exists(os.path.join(FRONTEND_PATH, path)):
            return send_from_directory(FRONTEND_PATH, path)
        else:
            # Return index.html for React Router
            return send_from_directory(FRONTEND_PATH, 'index.html')
    else:
        return "Frontend build not found", 404

# API Routes
@app.route('/api/compile', methods=['POST'])
def api_compile_code():
    """API endpoint to compile and run Python, C++ or JavaScript code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        syntax_only = data.get('syntax_only', False)
        timeout = data.get('timeout', 30)
        language = data.get('language', None)
        
        # Auto-detect language if not specified
        if not language:
            language = detect_language(code)
        
        logger.info(f"Compiling code in language: {language}")
        
        # Select appropriate compiler
        if language == 'cpp':
            if not cpp_compiler:
                return jsonify({
                    'success': False,
                    'error': 'C++ compiler not initialized. Make sure Docker is running.'
                }), 500
            compiler = cpp_compiler
            format_function = format_cpp_compiler_output
        elif language == 'js' or language == 'javascript':
            if not js_compiler:
                return jsonify({
                    'success': False,
                    'error': 'JavaScript compiler not initialized. Make sure Docker is running.'
                }), 500
            compiler = js_compiler
            format_function = format_js_compiler_output
        else:
            if not python_compiler:
                return jsonify({
                    'success': False,
                    'error': 'Python compiler not initialized. Make sure Docker is running.'
                }), 500
            compiler = python_compiler
            format_function = format_compiler_output
        
        # Compile and run the code
        if syntax_only:
            result = compiler.check_syntax(code)
        else:
            result = compiler.compile_and_run(code, timeout=timeout)
        
        # Format the response for the React frontend
        response = {
            'success': result.success,
            'output': result.output.split('\n') if result.output else [],
            'errors': result.error.split('\n') if result.error else [],
            'exit_code': result.exit_code,
            'execution_time': result.execution_time,
            'language': language,
            'timestamp': None,  # Will be set by frontend
            'formatted_output': format_function(result)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in compile endpoint: {e}")
        return jsonify({
            'success': False,
            'output': [],
            'errors': [str(e)],
            'exit_code': -1,
            'execution_time': 0.0,
            'language': 'unknown',
            'formatted_output': f"Error: {str(e)}"
        }), 500

# Legacy endpoint for backward compatibility
@app.route('/compile', methods=['POST'])
def compile_code():
    """Legacy endpoint - redirects to API"""
    return api_compile_code()

@app.route('/api/health')
def api_health_check():
    """Health check endpoint for the API"""
    python_status = "running" if python_compiler else "not initialized"
    cpp_status = "running" if cpp_compiler else "not initialized"
    js_status = "running" if js_compiler else "not initialized"
    return jsonify({
        'status': 'healthy',
        'compilers': {
            'python': python_status,
            'cpp': cpp_status,
            'javascript': js_status
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return api_health_check()

@app.route('/api/languages')
def api_supported_languages():
    """Get list of supported languages"""
    languages = []
    if python_compiler:
        languages.append({
            'id': 'python',
            'name': 'Python',
            'description': 'Python 3.9 with full standard library',
            'example': 'print("Hello, Python!")'
        })
    if cpp_compiler:
        languages.append({
            'id': 'cpp',
            'name': 'C++',
            'description': 'C++17 with GCC compiler',
            'example': '#include <iostream>\nint main() {\n    std::cout << "Hello, C++!" << std::endl;\n    return 0;\n}'
        })
    if js_compiler:
        languages.append({
            'id': 'javascript',
            'name': 'JavaScript',
            'description': 'Node.js 18 with modern JavaScript features',
            'example': 'console.log("Hello, JavaScript!");'
        })
    
    return jsonify({
        'languages': languages,
        'total': len(languages)
    })

@app.route('/images')
def list_images():
    """List available Docker images"""
    images_info = {}
    
    if python_compiler:
        try:
            images_info['python'] = python_compiler.get_available_images()
        except Exception as e:
            images_info['python'] = f"Error: {str(e)}"
    else:
        images_info['python'] = "Python compiler not initialized"
    
    if cpp_compiler:
        try:
            images_info['cpp'] = cpp_compiler.get_available_images()
        except Exception as e:
            images_info['cpp'] = f"Error: {str(e)}"
    else:
        images_info['cpp'] = "C++ compiler not initialized"
    
    if js_compiler:
        try:
            images_info['js'] = js_compiler.get_available_images()
        except Exception as e:
            images_info['js'] = f"Error: {str(e)}"
    else:
        images_info['js'] = "JavaScript compiler not initialized"
    
    return jsonify({'images': images_info})

if __name__ == '__main__':
    # Production configuration for Railway
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    # Initialize compilers on startup
    logger.info("🚀 Starting Unified Docker Compiler Backend...")
    
    if init_compilers():
        logger.info("✅ All compilers initialized successfully")
        logger.info("📋 Supported languages: Python, C++, JavaScript")
        logger.info(f"🌐 Server starting on port {port}")
        logger.info("🔧 API Base URL: /api")
        logger.info("📖 Available endpoints:")
        logger.info("   POST /api/compile - Compile and run code")
        logger.info("   GET  /api/health  - Health check")
        logger.info("   GET  /api/languages - Supported languages")
        app.run(debug=debug, host='0.0.0.0', port=port)
    else:
        logger.warning("⚠️  Some compilers failed to initialize")
        logger.info("🐳 Check that Docker is available")
        logger.info("🔄 Starting server anyway...")
        app.run(debug=debug, host='0.0.0.0', port=port)
