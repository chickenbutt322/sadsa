import subprocess
import tempfile
import os
import time
import ast
import sys
import base64
import binascii
import json
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List

class LanguageHandler(ABC):
    """Abstract base class for language handlers"""
    
    @abstractmethod
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute code and return result"""
        pass
    
    @abstractmethod
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate code syntax"""
        pass
    
    @abstractmethod
    def get_language_info(self) -> Dict[str, str]:
        """Get language information"""
        pass

class PythonHandler(LanguageHandler):
    """Handler for Python code execution"""
    
    def __init__(self):
        self.timeout = 30  # 30 seconds timeout
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely"""
        start_time = time.time()
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute Python code with timeout
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tempfile.gettempdir()
                )
                
                execution_time = time.time() - start_time
                
                return {
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None,
                    'execution_time': round(execution_time, 3)
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax Error: {str(e)}"
        except Exception as e:
            return False, f"Validation Error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Python language information"""
        return {
            'name': 'Python',
            'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'file_extension': '.py',
            'monaco_language': 'python'
        }

class JavaScriptHandler(LanguageHandler):
    """Handler for JavaScript code execution using Node.js"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js"""
        start_time = time.time()
        
        try:
            # Check if Node.js is available
            subprocess.run(['node', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Node.js is not installed on this system',
                'execution_time': 0
            }
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute JavaScript code
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tempfile.gettempdir()
                )
                
                execution_time = time.time() - start_time
                
                return {
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None,
                    'execution_time': round(execution_time, 3)
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate JavaScript syntax using Node.js"""
        try:
            # Use Node.js syntax check
            result = subprocess.run(
                ['node', '--check'],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # If Node.js is not available or check fails, return basic validation
            return True, "Syntax validation not available (Node.js required)"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get JavaScript language information"""
        return {
            'name': 'JavaScript',
            'version': 'Node.js',
            'file_extension': '.js',
            'monaco_language': 'javascript'
        }

class CHandler(LanguageHandler):
    """Handler for C code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute C code"""
        start_time = time.time()
        
        try:
            # Check if GCC is available
            subprocess.run(['gcc', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'GCC compiler is not installed on this system',
                'execution_time': 0
            }
        
        try:
            # Create temporary C file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Compile
            exe_file = temp_file.replace('.c', '')
            compile_result = subprocess.run(
                ['gcc', temp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if compile_result.returncode != 0:
                return {
                    'output': '',
                    'error': f'Compilation Error:\n{compile_result.stderr}',
                    'execution_time': time.time() - start_time
                }
            
            # Execute
            result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            execution_time = time.time() - start_time
            
            # Cleanup
            try:
                os.unlink(temp_file)
                os.unlink(exe_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'execution_time': round(execution_time, 3)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate C syntax"""
        try:
            # Try syntax check with gcc
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['gcc', '-fsyntax-only', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get C language information"""
        return {
            'name': 'C',
            'version': 'GCC',
            'file_extension': '.c',
            'monaco_language': 'c'
        }

class JavaHandler(LanguageHandler):
    """Handler for Java code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Java code"""
        start_time = time.time()
        
        try:
            # Check if Java is available
            subprocess.run(['javac', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Java compiler (javac) is not installed on this system',
                'execution_time': 0
            }
        
        try:
            # Extract class name from code
            class_name = 'Main'  # Default
            lines = code.split('\n')
            for line in lines:
                if 'public class' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        class_name = parts[2]
                    break
            
            # Create temporary Java file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Rename to match class name
            java_file = os.path.join(os.path.dirname(temp_file), f'{class_name}.java')
            os.rename(temp_file, java_file)
            
            # Compile
            compile_result = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=os.path.dirname(java_file)
            )
            
            if compile_result.returncode != 0:
                return {
                    'output': '',
                    'error': f'Compilation Error:\n{compile_result.stderr}',
                    'execution_time': time.time() - start_time
                }
            
            # Execute
            result = subprocess.run(
                ['java', class_name],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(java_file)
            )
            
            execution_time = time.time() - start_time
            
            # Cleanup
            try:
                os.unlink(java_file)
                class_file = os.path.join(os.path.dirname(java_file), f'{class_name}.class')
                os.unlink(class_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'execution_time': round(execution_time, 3)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Java syntax"""
        return True, "Java syntax validation available after compilation"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Java language information"""
        return {
            'name': 'Java',
            'version': 'OpenJDK',
            'file_extension': '.java',
            'monaco_language': 'java'
        }

class GoHandler(LanguageHandler):
    """Handler for Go code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Go code"""
        start_time = time.time()
        
        try:
            # Check if Go is available
            subprocess.run(['go', 'version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Go compiler is not installed on this system',
                'execution_time': 0
            }
        
        try:
            # Create temporary Go file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute Go code directly
            result = subprocess.run(
                ['go', 'run', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            execution_time = time.time() - start_time
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'execution_time': round(execution_time, 3)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Go syntax"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['go', 'fmt', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Go language information"""
        return {
            'name': 'Go',
            'version': 'Go',
            'file_extension': '.go',
            'monaco_language': 'go'
        }

class RustHandler(LanguageHandler):
    """Handler for Rust code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Rust code"""
        start_time = time.time()
        
        try:
            # Check if Rust is available
            subprocess.run(['rustc', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Rust compiler (rustc) is not installed on this system',
                'execution_time': 0
            }
        
        try:
            # Create temporary Rust file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Compile
            exe_file = temp_file.replace('.rs', '')
            compile_result = subprocess.run(
                ['rustc', temp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if compile_result.returncode != 0:
                return {
                    'output': '',
                    'error': f'Compilation Error:\n{compile_result.stderr}',
                    'execution_time': time.time() - start_time
                }
            
            # Execute
            result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            execution_time = time.time() - start_time
            
            # Cleanup
            try:
                os.unlink(temp_file)
                os.unlink(exe_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'execution_time': round(execution_time, 3)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Rust syntax"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['rustc', '--check-cfg', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Rust language information"""
        return {
            'name': 'Rust',
            'version': 'Rustc',
            'file_extension': '.rs',
            'monaco_language': 'rust'
        }

class EncodingHandler(LanguageHandler):
    """Handler for encoding/decoding operations"""
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute encoding/decoding operations"""
        start_time = time.time()
        
        try:
            # Parse the operation
            lines = code.strip().split('\n')
            if not lines:
                return {
                    'output': '',
                    'error': 'No operation specified',
                    'execution_time': 0
                }
            
            operation = lines[0].strip().lower()
            data = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            
            if operation.startswith('base64 encode'):
                result = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                output = f"Base64 Encoded:\n{result}"
                
            elif operation.startswith('base64 decode'):
                try:
                    result = base64.b64decode(data).decode('utf-8')
                    output = f"Base64 Decoded:\n{result}"
                except Exception as e:
                    return {
                        'output': '',
                        'error': f'Base64 decode error: {str(e)}',
                        'execution_time': time.time() - start_time
                    }
                    
            elif operation.startswith('url encode'):
                result = urllib.parse.quote(data)
                output = f"URL Encoded:\n{result}"
                
            elif operation.startswith('url decode'):
                try:
                    result = urllib.parse.unquote(data)
                    output = f"URL Decoded:\n{result}"
                except Exception as e:
                    return {
                        'output': '',
                        'error': f'URL decode error: {str(e)}',
                        'execution_time': time.time() - start_time
                    }
                    
            elif operation.startswith('hex encode'):
                result = data.encode('utf-8').hex()
                output = f"Hex Encoded:\n{result}"
                
            elif operation.startswith('hex decode'):
                try:
                    result = bytes.fromhex(data).decode('utf-8')
                    output = f"Hex Decoded:\n{result}"
                except Exception as e:
                    return {
                        'output': '',
                        'error': f'Hex decode error: {str(e)}',
                        'execution_time': time.time() - start_time
                    }
                    
            elif operation.startswith('json format'):
                try:
                    parsed = json.loads(data)
                    result = json.dumps(parsed, indent=2)
                    output = f"JSON Formatted:\n{result}"
                except Exception as e:
                    return {
                        'output': '',
                        'error': f'JSON format error: {str(e)}',
                        'execution_time': time.time() - start_time
                    }
                    
            elif operation.startswith('data url'):
                # Create data URL
                mime_type = 'text/plain'
                if 'image' in operation:
                    mime_type = 'image/png'
                elif 'html' in operation:
                    mime_type = 'text/html'
                
                encoded_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                result = f"data:{mime_type};base64,{encoded_data}"
                output = f"Data URL:\n{result}"
                
            else:
                available_ops = [
                    "base64 encode", "base64 decode",
                    "url encode", "url decode", 
                    "hex encode", "hex decode",
                    "json format", "data url"
                ]
                return {
                    'output': '',
                    'error': f'Unknown operation: {operation}\nAvailable operations: {", ".join(available_ops)}',
                    'execution_time': time.time() - start_time
                }
            
            return {
                'output': output,
                'error': None,
                'execution_time': round(time.time() - start_time, 3)
            }
            
        except Exception as e:
            return {
                'output': '',
                'error': f'Encoding error: {str(e)}',
                'execution_time': time.time() - start_time
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate encoding operation"""
        lines = code.strip().split('\n')
        if not lines:
            return False, "No operation specified"
        
        operation = lines[0].strip().lower()
        valid_ops = ['base64 encode', 'base64 decode', 'url encode', 'url decode', 
                    'hex encode', 'hex decode', 'json format', 'data url']
        
        if not any(operation.startswith(op) for op in valid_ops):
            return False, f"Invalid operation. Available: {', '.join(valid_ops)}"
        
        return True, None
    
    def get_language_info(self) -> Dict[str, str]:
        """Get encoding handler information"""
        return {
            'name': 'Encoding/Decoding',
            'version': 'Built-in',
            'file_extension': '.txt',
            'monaco_language': 'plaintext'
        }

class LanguageHandlerFactory:
    """Factory class for managing language handlers"""
    
    def __init__(self):
        self._handlers = {
            'python': PythonHandler(),
            'javascript': JavaScriptHandler(),
            'js': JavaScriptHandler(),  # Alias for JavaScript
            'c': CHandler(),
            'java': JavaHandler(),
            'go': GoHandler(),
            'rust': RustHandler(),
            'encoding': EncodingHandler(),
            'encode': EncodingHandler(),  # Alias
        }
    
    def get_handler(self, language: str) -> Optional[LanguageHandler]:
        """Get handler for specified language"""
        return self._handlers.get(language.lower())
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages"""
        languages = []
        seen = set()
        
        for lang_key, handler in self._handlers.items():
            info = handler.get_language_info()
            lang_name = info['name']
            
            # Avoid duplicates (e.g., js and javascript)
            if lang_name not in seen:
                languages.append({
                    'key': lang_key,
                    'name': lang_name,
                    'version': info['version'],
                    'monaco_language': info['monaco_language']
                })
                seen.add(lang_name)
        
        return sorted(languages, key=lambda x: x['name'])
    
    def register_handler(self, language: str, handler: LanguageHandler):
        """Register a new language handler"""
        self._handlers[language.lower()] = handler
import subprocess
import os
import tempfile
import logging

# Add missing implementations for C, Go, and Rust handlers
class CHandler(LanguageHandler):
    """Handler for C code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute C code"""
        start_time = time.time()
        
        try:
            # Check if GCC is available
            subprocess.run(['gcc', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'GCC compiler is not installed on this system',
                'exit_code': 1
            }
        
        try:
            # Create temporary C file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Compile
            exe_file = temp_file.replace('.c', '')
            compile_result = subprocess.run(
                ['gcc', temp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if compile_result.returncode != 0:
                return {
                    'output': '',
                    'error': f'Compilation Error:\n{compile_result.stderr}',
                    'exit_code': compile_result.returncode
                }
            
            # Execute
            result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            # Cleanup
            try:
                os.unlink(temp_file)
                os.unlink(exe_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else '',
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'exit_code': 1
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'exit_code': 1
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate C syntax"""
        try:
            # Try syntax check with gcc
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['gcc', '-fsyntax-only', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get C language information"""
        return {
            'name': 'C',
            'version': 'GCC',
            'file_extension': '.c',
            'monaco_language': 'c'
        }

class GoHandler(LanguageHandler):
    """Handler for Go code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Go code"""
        start_time = time.time()
        
        try:
            # Check if Go is available
            subprocess.run(['go', 'version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Go is not installed on this system',
                'exit_code': 1
            }
        
        try:
            # Create temporary Go file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute Go code directly
            result = subprocess.run(
                ['go', 'run', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else '',
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'exit_code': 1
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'exit_code': 1
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Go syntax"""
        try:
            # Try syntax check with go fmt
            result = subprocess.run(
                ['go', 'fmt'],
                input=code,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return True, None  # Basic validation
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Go language information"""
        return {
            'name': 'Go',
            'version': 'Go',
            'file_extension': '.go',
            'monaco_language': 'go'
        }

class RustHandler(LanguageHandler):
    """Handler for Rust code execution"""
    
    def __init__(self):
        self.timeout = 30
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Rust code"""
        start_time = time.time()
        
        try:
            # Check if Rust is available
            subprocess.run(['rustc', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'output': '',
                'error': 'Rust compiler is not installed on this system',
                'exit_code': 1
            }
        
        try:
            # Create temporary Rust file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Compile
            exe_file = temp_file.replace('.rs', '')
            compile_result = subprocess.run(
                ['rustc', temp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if compile_result.returncode != 0:
                return {
                    'output': '',
                    'error': f'Compilation Error:\n{compile_result.stderr}',
                    'exit_code': compile_result.returncode
                }
            
            # Execute
            result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            # Cleanup
            try:
                os.unlink(temp_file)
                os.unlink(exe_file)
            except OSError:
                pass
            
            return {
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else '',
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Code execution timed out after {self.timeout} seconds',
                'exit_code': 1
            }
        except Exception as e:
            return {
                'output': '',
                'error': f'Execution error: {str(e)}',
                'exit_code': 1
            }
    
    def validate(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Rust syntax"""
        try:
            # Try syntax check with rustc
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['rustc', '--emit=metadata', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_language_info(self) -> Dict[str, str]:
        """Get Rust language information"""
        return {
            'name': 'Rust',
            'version': 'Rust',
            'file_extension': '.rs',
            'monaco_language': 'rust'
        }

# Updated factory with working handlers
class LanguageHandlerFactory:
    """Factory class for managing language handlers"""
    
    def __init__(self):
        self.handlers = {
            'python': PythonHandler(),
            'javascript': JavaScriptHandler(), 
            'java': JavaHandler(),
            'c': CHandler(),
            'go': GoHandler(),
            'rust': RustHandler(),
        }
    
    def get_handler(self, language: str):
        """Get handler for specified language"""
        return self.handlers.get(language.lower())
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return list(self.handlers.keys())
    
    def get_available_languages(self):
        """Get list of available languages with info"""
        languages = []
        for lang, handler in self.handlers.items():
            try:
                info = handler.get_language_info()
                info['key'] = lang
                languages.append(info)
            except:
                # Fallback info if handler doesn't have get_language_info
                languages.append({
                    'key': lang,
                    'name': lang.capitalize(),
                    'version': 'Unknown',
                    'file_extension': f'.{lang}',
                    'monaco_language': lang
                })
        return languages


