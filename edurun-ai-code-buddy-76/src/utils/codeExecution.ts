interface ExecutionResult {
  output: string[];
  errors: string[];
  timestamp: Date;
  executionTime: number;
}

interface CompilerResponse {
  success: boolean;
  output: string[];
  errors: string[];
  exit_code: number;
  execution_time: number;
  language: string;
  formatted_output: string;
}

// Backend API configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Map frontend language names to backend language names
const LANGUAGE_MAP: Record<string, string> = {
  'javascript': 'javascript',
  'js': 'javascript',
  'python': 'python',
  'cpp': 'cpp',
  'c++': 'cpp'
};

export const executeCode = async (code: string, language: string = 'javascript'): Promise<ExecutionResult> => {
  const startTime = Date.now();
  
  try {
    // Map language to backend format
    const backendLanguage = LANGUAGE_MAP[language.toLowerCase()] || language;
    
    const response = await fetch(`${API_BASE_URL}/compile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        language: backendLanguage,
        timeout: 30,
        syntax_only: false
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: CompilerResponse = await response.json();
    
    return {
      output: result.output || [],
      errors: result.errors || [],
      timestamp: new Date(),
      executionTime: result.execution_time || (Date.now() - startTime) / 1000
    };

  } catch (error) {
    console.error('Code execution error:', error);
    
    return {
      output: [],
      errors: [
        `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'Make sure the backend server is running on http://localhost:5000'
      ],
      timestamp: new Date(),
      executionTime: (Date.now() - startTime) / 1000
    };
  }
};

// Legacy function for backward compatibility
export const executeJavaScript = async (code: string): Promise<ExecutionResult> => {
  return executeCode(code, 'javascript');
};

// Multi-language execution functions
export const executePython = async (code: string): Promise<ExecutionResult> => {
  return executeCode(code, 'python');
};

export const executeCpp = async (code: string): Promise<ExecutionResult> => {
  return executeCode(code, 'cpp');
};

// Check syntax only
export const checkSyntax = async (code: string, language: string): Promise<ExecutionResult> => {
  try {
    const backendLanguage = LANGUAGE_MAP[language.toLowerCase()] || language;
    
    const response = await fetch(`${API_BASE_URL}/compile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        language: backendLanguage,
        timeout: 10,
        syntax_only: true
      })
    });

    const result: CompilerResponse = await response.json();
    
    return {
      output: result.success ? ['✅ Syntax is valid'] : [],
      errors: result.errors || [],
      timestamp: new Date(),
      executionTime: result.execution_time || 0
    };

  } catch (error) {
    return {
      output: [],
      errors: [`Syntax check failed: ${error instanceof Error ? error.message : 'Unknown error'}`],
      timestamp: new Date(),
      executionTime: 0
    };
  }
};

// Get supported languages from backend
export const getSupportedLanguages = async (): Promise<Array<{id: string, name: string, description: string, example: string}>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/languages`);
    const result = await response.json();
    return result.languages || [];
  } catch (error) {
    console.error('Failed to fetch supported languages:', error);
    return [
      {
        id: 'javascript',
        name: 'JavaScript',
        description: 'JavaScript (fallback - backend not available)',
        example: 'console.log("Hello, World!");'
      }
    ];
  }
};

// Health check
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const result = await response.json();
    return result.status === 'healthy';
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
};

