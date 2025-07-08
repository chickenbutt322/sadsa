class CodeEditor {
    constructor() {
        this.editor = null;
        this.currentLanguage = 'python';
        this.currentFile = 'filename.py';
        this.isEditorReady = false;
    }

    async initializeEditor() {
        console.log('Initializing Monaco editor...');

        return new Promise((resolve) => {
            // Mobile sidebar toggle
            document.addEventListener('DOMContentLoaded', () => {
                const toggleBtn = document.getElementById('toggleSidebar');
                const sidebar = document.getElementById('sidebar');

                if (toggleBtn && sidebar) {
                    toggleBtn.addEventListener('click', () => {
                        const icon = toggleBtn.querySelector('i');
                        sidebar.style.maxHeight = sidebar.style.maxHeight === '80px' || sidebar.style.maxHeight === '' ? '40vh' : '80px';
                        icon.className = sidebar.style.maxHeight === '40vh' ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
                    });
                }
            });

            // Initialize Monaco Editor
            require.config({
                paths: {
                    'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs'
                }
            });

            require(['vs/editor/editor.main'], () => {
                console.log('Monaco editor loaded');

                const editorElement = document.getElementById('monaco-editor');
                if (!editorElement) {
                    console.error('Editor element not found');
                    return;
                }

                this.editor = monaco.editor.create(editorElement, {
                    value: '# Welcome to CodeCraft Studio!\n# Write your Python code here\n\nprint("Hello, World!")',
                    language: this.currentLanguage,
                    theme: 'vs-dark',
                    fontSize: 14,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    roundedSelection: false,
                    readOnly: false,
                    cursorStyle: 'line',
                    glyphMargin: true,
                    folding: true,
                    showFoldingControls: 'always',
                    scrollbar: {
                        vertical: 'visible',
                        horizontal: 'visible',
                        useShadows: false,
                        verticalHasArrows: true,
                        horizontalHasArrows: true
                    }
                });

                console.log('Monaco editor created successfully');
                this.isEditorReady = true;

                // Handle window resize
                window.addEventListener('resize', () => {
                    if (this.editor) {
                        this.editor.layout();
                    }
                });

                // Force layout after multiple delays to ensure container is ready
                setTimeout(() => { if (this.editor) this.editor.layout(); }, 100);
                setTimeout(() => { if (this.editor) this.editor.layout(); }, 500);
                setTimeout(() => { if (this.editor) this.editor.layout(); }, 1000);

                resolve(this.editor);
            });
        });
    }

    changeLanguage(language) {
        this.currentLanguage = language;
        if (this.editor) {
            const model = this.editor.getModel();
            monaco.editor.setModelLanguage(model, this.currentLanguage);

            // Update the default code template for new language
            this.editor.setValue(this.getDefaultCode(language));
        }
    }

    getDefaultCode(language) {
        const templates = {
            python: '# Welcome to CodeCraft Studio!\nprint("Hello, World!")',
            javascript: '// Write your JavaScript code here\nconsole.log("Hello, World!");',
            java: '// Write your Java code here\npublic class Main { public static void main(String[] args) { System.out.println("Hello, World!"); } }',
            c: '// Write your C code here\n#include <stdio.h>\nint main() { printf("Hello, World!\\n"); return 0; }',
            go: '// Write your Go code here\npackage main\nimport "fmt"\nfunc main() { fmt.Println("Hello, World!") }',
            rust: '// Write your Rust code here\nfn main() { println!("Hello, World!"); }'
        };
        return templates[language] || templates['python'];
    }
}

// Application initialization
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM loaded, initializing CodeCraft Studio...');

    const codeEditor = new CodeEditor();

    try {
        await codeEditor.initializeEditor();
        
        // Set up language switching
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                const newLanguage = e.target.value;
                codeEditor.changeLanguage(newLanguage);
                updateFilename(newLanguage);
            });
        }

        // Set up run button
        const runButton = document.getElementById('run-button');
        if (runButton) {
            runButton.addEventListener('click', () => {
                runCode(codeEditor);
            });
        }

        // Set up save button
        const saveButton = document.getElementById('save-button');
        if (saveButton) {
            saveButton.addEventListener('click', () => {
                saveCode(codeEditor);
            });
        }

    } catch (error) {
        console.error('Error initializing the editor:', error);
    }
});

// Helper function to update filename based on language
function updateFilename(language) {
    const extensions = {
        python: '.py',
        javascript: '.js',
        java: '.java',
        c: '.c',
        go: '.go',
        rust: '.rs'
    };
    
    const filename = 'main' + (extensions[language] || '.txt');
    const filenameDisplay = document.querySelector('.current-file');
    if (filenameDisplay) {
        filenameDisplay.textContent = filename;
    }
}

// Function to run code
async function runCode(codeEditor) {
    if (!codeEditor.isEditorReady) {
        console.error('Editor is not ready');
        return;
    }

    const code = codeEditor.editor.getValue();
    const language = codeEditor.currentLanguage;
    const outputDiv = document.getElementById('output');
    const runButton = document.getElementById('run-button');

    // Show loading state
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Running...';
    outputDiv.innerHTML = '<div class="text-muted"><i class="fas fa-spinner fa-spin me-1"></i>Executing code...</div>';

    try {
        const response = await fetch('/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            // Display output
            let outputHtml = '';
            if (result.output) {
                outputHtml += `<div class="output-section"><strong>Output:</strong><pre>${escapeHtml(result.output)}</pre></div>`;
            }
            if (result.error) {
                outputHtml += `<div class="output-section error"><strong>Error:</strong><pre>${escapeHtml(result.error)}</pre></div>`;
            }
            if (result.execution_time) {
                outputHtml += `<div class="output-section"><small class="text-muted">Execution time: ${result.execution_time.toFixed(3)}s</small></div>`;
            }
            
            outputDiv.innerHTML = outputHtml || '<div class="text-muted">No output</div>';
        } else {
            outputDiv.innerHTML = `<div class="error">Error: ${escapeHtml(result.error || 'Unknown error')}</div>`;
        }
    } catch (error) {
        console.error('Error running code:', error);
        outputDiv.innerHTML = `<div class="error">Network error: ${escapeHtml(error.message)}</div>`;
    } finally {
        // Reset button state
        runButton.disabled = false;
        runButton.innerHTML = '<i class="fas fa-play me-1"></i>Run';
    }
}

// Function to save code
async function saveCode(codeEditor) {
    if (!codeEditor.isEditorReady) {
        console.error('Editor is not ready');
        return;
    }

    const code = codeEditor.editor.getValue();
    const language = codeEditor.currentLanguage;
    const saveButton = document.getElementById('save-button');

    // Show loading state
    saveButton.disabled = true;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';

    try {
        const response = await fetch('/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                language: language,
                name: 'Untitled Project'
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            // Show success message
            showNotification('Code saved successfully!', 'success');
        } else {
            showNotification(result.error || 'Failed to save code', 'error');
        }
    } catch (error) {
        console.error('Error saving code:', error);
        showNotification('Network error while saving', 'error');
    } finally {
        // Reset button state
        saveButton.disabled = false;
        saveButton.innerHTML = '<i class="fas fa-save me-1"></i>Save';
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}