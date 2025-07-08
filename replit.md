# CodeCraft Studio IDE

## Overview

CodeCraft Studio is a web-based multi-language IDE built with Flask. It provides a complete development environment with code editing, execution, user authentication, and project management capabilities. The application features a dark-themed interface with Monaco Editor for code editing and supports multiple programming languages.

## System Architecture

### Frontend Architecture
- **Framework**: Pure HTML/CSS/JavaScript with Bootstrap 5 for UI components
- **Code Editor**: Monaco Editor for syntax highlighting and code editing
- **Theme**: Dark theme with responsive design
- **Mobile Support**: Responsive layout with collapsible sidebar for mobile devices

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with session management
- **Email Service**: Flask-Mail for email verification and password reset
- **Security**: CSRF protection with Flask-WTF

### Database Schema
- **Users**: User accounts with authentication, email verification, and 2FA support
- **Projects**: User project management
- **ProjectFiles**: File storage within projects
- **CodeSnippets**: Reusable code snippets

## Key Components

### Authentication System
- **User Registration**: Email-based account creation with verification
- **Login/Logout**: Session-based authentication
- **Password Reset**: Token-based password recovery via email
- **Two-Factor Authentication**: TOTP-based 2FA with QR code generation
- **Email Verification**: Standalone verification site for email confirmation

### Code Execution Engine
- **Language Support**: Extensible language handler system
- **Python Handler**: Secure code execution with timeout protection
- **Sandboxed Execution**: Temporary file-based execution with subprocess isolation
- **Error Handling**: Comprehensive error capture and reporting

### Project Management
- **File Operations**: Create, edit, and manage project files
- **Code Snippets**: Save and reuse code snippets
- **Project Organization**: Hierarchical project structure

### Email System
- **SMTP Configuration**: Outlook/Hotmail integration
- **Templates**: HTML and text email templates
- **Verification Flow**: Automated email verification process

## Data Flow

1. **User Registration**:
   - User submits registration form
   - System creates unverified user account
   - Verification email sent with token
   - User clicks verification link or enters token manually
   - Account activated upon successful verification

2. **Code Execution**:
   - User writes code in Monaco editor
   - Code submitted to language handler
   - Handler creates temporary file and executes code
   - Results captured and returned to frontend
   - Output displayed in result panel

3. **Project Management**:
   - Users create projects and files
   - Files stored in database with content
   - Real-time editing with Monaco editor
   - Auto-save functionality

## External Dependencies

### Core Dependencies
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Flask-Mail**: Email functionality
- **Flask-WTF**: CSRF protection
- **Werkzeug**: Security utilities

### Frontend Dependencies
- **Monaco Editor**: Code editor (CDN)
- **Bootstrap 5**: UI framework (CDN)
- **Font Awesome**: Icon library (CDN)

### Security Dependencies
- **pyotp**: TOTP for 2FA
- **qrcode**: QR code generation
- **itsdangerous**: Token generation

## Deployment Strategy

### Development Environment
- **Database**: PostgreSQL with full authentication and project management
- **Static Files**: Served directly by Flask
- **Email**: Configured for Outlook SMTP

### Production Considerations
- **Database**: PostgreSQL with authentication and Google OAuth integration
- **Static Files**: Can be served by CDN
- **Email**: Environment-based configuration
- **Security**: SSL/TLS termination and secure headers

### Verification Site
- **Standalone Deployment**: Separate static site for email verification
- **Deployment Options**: Netlify, Vercel, or similar static hosting
- **Cross-Origin**: Configured for API communication with main application

## Changelog

```
Changelog:
- July 08, 2025. Initial setup
- July 08, 2025. Added Google OAuth authentication with complete sign-in flow
- July 08, 2025. Migrated from SQLite to PostgreSQL database with full schema
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

### Development Setup
- Database initialization scripts provided (`fix_database.py`, `reset_db.py`)
- Account management utilities (`list_accounts.py`, `delete_all_accounts.py`)
- Development-friendly CSRF configuration for Replit environment

### Security Features
- Password hashing with Werkzeug
- Email verification required for account activation
- TOTP-based two-factor authentication
- CSRF protection on forms
- Session-based authentication

### Code Editor Features
- Syntax highlighting for multiple languages
- Dark theme optimized for coding
- Auto-completion and error detection
- Real-time code execution
- Mobile-responsive design