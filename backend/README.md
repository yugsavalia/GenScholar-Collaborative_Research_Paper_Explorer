# Django Workspace Project

A comprehensive Django application that combines real-time chat functionality, PDF file sharing, and collaborative workspace management. This project implements WebSocket-based communication for live chat features and provides an integrated PDF viewer for document sharing.

## Features

1. **User Authentication**
   - Secure user registration and authentication system
   - Login and logout functionality
   - User profile management
   
2. **Workspaces**
   - Create and manage collaborative workspaces
   - Dashboard view of all workspaces
   - Detailed workspace view with member list
   - Access control and permissions management
   
3. **PDF Management**
   - Upload and store PDF files within workspaces
   - Built-in PDF viewer using custom JavaScript
   - Organize documents by workspace
   - Secure file access controls
   
4. **Real-time Chat**
   - WebSocket-based live chat functionality
   - Workspace-specific chat rooms
   - Real-time message updates
   - Chat history preservation
   
5. **User Invitations**
   - Invite users to join workspaces
   - Manage workspace memberships
   - Role-based access control

## Technical Requirements

- Python 3.8 or higher
- Django 5.2.7
- Channels 4.0.0 for WebSocket support
- Daphne 4.1.2 as the ASGI server
- Pillow 10.2.0 for image processing

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cursortest
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create a superuser (optional but recommended):
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:

   **IMPORTANT**: This project requires Daphne ASGI server for WebSocket support:

   ```bash
   # For development:
   daphne -b 0.0.0.0 -p 8000 cursortest.asgi:application

   # For production (using Unix/Linux):
   daphne -u /tmp/daphne.sock cursortest.asgi:application
   
   # For Windows production:
   daphne -b 127.0.0.1 -p 8000 cursortest.asgi:application
   ```

   Note: The standard `python manage.py runserver` command will NOT support WebSockets properly. Always use Daphne for running this application.

7. Access the application:
   - Development: Open http://localhost:8000 in your browser
   - Production: Configure your web server (nginx/Apache) to proxy to Daphne

## Project Structure

The project is organized into several Django apps, each handling specific functionality:

- **accounts/**
  - Handles user authentication and management
  - Custom user registration and login views
  - User profile templates
  
- **workspaces/**
  - Manages collaborative workspace functionality
  - Dashboard and workspace detail views
  - Workspace member management
  - Templates for workspace interfaces
  
- **pdfs/**
  - Handles PDF file upload and storage
  - Custom PDF viewer implementation
  - File management within workspaces
  - Static files for PDF viewing
  
- **chat/**
  - Implements real-time chat functionality
  - WebSocket consumers for live messaging
  - Chat history management
  - Workspace-specific chat rooms

## Usage Guide

1. **Getting Started**
   - Register a new account at `/accounts/signup/`
   - Log in at `/accounts/login/`
   - Access your dashboard at `/workspaces/dashboard/`

2. **Managing Workspaces**
   - Create a new workspace from the dashboard
   - View workspace details and members
   - Manage workspace settings and permissions
   - Invite new members using their email addresses

3. **Working with PDFs**
   - Upload PDFs from the workspace detail view
   - View PDFs using the built-in viewer
   - Organize documents within workspaces
   - Download shared PDFs

4. **Using the Chat Feature**
   - Access workspace-specific chat rooms
   - Send and receive real-time messages
   - View chat history
   - Receive notifications for new messages

## Production Deployment

For production deployment:

1. Configure your settings.py:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Set up proper database settings
   - Configure static and media file serving

2. Set up a reverse proxy (nginx/Apache) to:
   - Serve static and media files
   - Proxy WebSocket connections to Daphne
   - Handle SSL/TLS termination

3. Use process management:
   - Supervisor or systemd to manage Daphne
   - Configure proper logging
   - Set up proper security measures

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for any bugs or feature requests.

## License

[Specify your license here]

