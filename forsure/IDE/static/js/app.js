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
        // Language and UI setup...
    } catch (error) {
        console.error('Error initializing the editor:', error);
    }
});