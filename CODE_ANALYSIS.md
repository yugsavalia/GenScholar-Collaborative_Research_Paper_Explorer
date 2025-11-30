# CODE_ANALYSIS.md

## 1. One-line summary

GenScholar is a collaborative research paper exploration platform that transforms PDF documents into interactive workspaces where research teams can upload papers, generate AI-powered summaries, annotate text in real-time, hold threaded discussions on text selections, and chat with an AI assistant powered by the uploaded documents.

## 2. High-level architecture

GenScholar follows a modern full-stack architecture with a Django backend and React frontend, communicating via REST APIs and WebSockets.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vite)                     │
│  - React 18 + Vite build tool                                │
│  - API client with CSRF handling                             │
│  - WebSocket clients for real-time features                  │
│  - Deployed on Netlify (https://genscholar.netlify.app)    │
└──────────────────────┬────────────────────────────────────────┘
                      │
                      │ HTTPS (REST + WebSocket)
                      │ Cookies (Session Auth)
                      │ CSRF Tokens
                      │
┌──────────────────────▼────────────────────────────────────────┐
│              Backend (Django + Channels/ASGI)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  HTTP Layer (Django Views + DRF ViewSets)             │   │
│  │  - REST API endpoints                                 │   │
│  │  - Session-based authentication                       │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                         │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  WebSocket Layer (Channels)                           │   │
│  │  - Chat consumer (workspace_{id})                     │   │
│  │  - Thread consumer (threads_workspace_{id}_pdf_{id})  │   │
│  │  - Notification consumer (user_{id})                 │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                         │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │  Channel Layer (Redis or In-Memory)                    │   │
│  │  - Redis: Production (127.0.0.1:6379)                │   │
│  │  - In-Memory: Development fallback                    │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────┬────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  PostgreSQL  │ │   Redis   │ │   Email    │
│  Database    │ │  Channel  │ │   SMTP     │
│              │ │   Layer   │ │  (Gmail)   │
└──────────────┘ └───────────┘ └────────────┘
```

**Key Components:**

- **Frontend**: React 18 with Vite build tool, deployed on Netlify. Uses `@/` alias for `client/src/` directory.
- **Backend**: Django 5.2.7 with ASGI application (Channels) for WebSocket support. Deployed on Railway.
- **Realtime**: Django Channels with Redis channel layer (falls back to in-memory for development).
- **Database**: PostgreSQL in production, SQLite for local development (via `DATABASES` setting).
- **Email**: SMTP (Gmail) for verification emails, OTP codes, and password resets.
- **Storage**: 
  - PDFs stored as `BinaryField` in database (not filesystem)
  - FAISS vector indexes stored in `media/vector_indexes/workspace_index_{id}/`
  - Static files served via WhiteNoise in production

**Communication Flow:**

1. **REST API**: Frontend makes HTTP requests to Django endpoints. Session cookies maintain authentication. CSRF tokens required for state-changing requests (POST/PUT/PATCH/DELETE).
2. **WebSockets**: Frontend connects to WebSocket endpoints for real-time chat, thread updates, and notifications. Authentication via Django session middleware.
3. **CORS**: Configured for `http://localhost:5173` (dev) and `https://genscholar.netlify.app` (production).

## 3. Technologies used

**Backend:**
- `Django==5.2.7` - Web framework and ORM
- `channels==4.0.0` - WebSocket support via ASGI
- `daphne==4.1.2` - ASGI server (development)
- `djangorestframework==3.14.0` - REST API framework
- `django-cors-headers==4.3.1` - CORS middleware
- `channels-redis==4.1.0` - Redis channel layer backend
- `redis==5.0.1` - Redis client
- `django-allauth==0.57.0` - Authentication (email verification, Google OAuth)
- `django-background-tasks==1.2.8` - Background job processing
- `psycopg2-binary>=2.9` - PostgreSQL adapter
- `gunicorn==21.2.0` - WSGI/ASGI server (production)
- `uvicorn[standard]==0.24.0` - ASGI worker for Gunicorn
- `whitenoise==6.6.0` - Static file serving
- `langchain-google-genai>=2.0.0` - Google Gemini LLM integration
- `langchain-community>=0.3.0` - FAISS vector store
- `langchain-cohere>=0.1.0` - Cohere embeddings
- `pdfplumber>=0.11.0` - PDF text extraction
- `python-dotenv==1.0.0` - Environment variable loading

**Frontend:**
- `react==18.3.1` - UI framework
- `vite==5.4.20` - Build tool and dev server
- `wouter==3.3.5` - Lightweight routing
- `@tanstack/react-query==5.60.5` - Data fetching and caching
- `react-pdf==10.2.0` - PDF rendering
- `pdfjs-dist==5.4.296` - PDF.js library
- `@radix-ui/*` - UI component primitives
- `tailwindcss==3.4.17` - Utility-first CSS
- `formik==2.4.6` - Form management
- `zod==3.24.2` - Schema validation

## 4. Environment variables (detailed)

### Backend Environment Variables

All backend environment variables are loaded from `.env` file via `python-dotenv` in `backend/genscholar/settings.py` (line 17).

#### Required Variables

| Variable | Purpose | Example Value | Used In |
|----------|---------|---------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key for cryptographic signing | `django-insecure-...` | `settings.py:26` |
| `POSTGRES_DB` | PostgreSQL database name | `genscholar_db` | `settings.py:152` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` | `settings.py:153` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `your_password` | `settings.py:154` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` or Railway host | `settings.py:155` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | `settings.py:156` |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` | `settings.py:255` |
| `EMAIL_PORT` | SMTP server port | `587` | `settings.py:256` |
| `EMAIL_HOST_USER` | SMTP username (Gmail address) | `your-email@gmail.com` | `settings.py:257` |
| `EMAIL_HOST_PASSWORD` | SMTP password (Gmail App Password) | `your_app_password` | `settings.py:258` |
| `GEMINI_API_KEY` | Google Gemini API key for chatbot | `AIza...` | `settings.py:272`, `chatbot/engine.py:254` |
| `COHERE_API_KEY` | Cohere API key for embeddings | `cohere_api_key...` | `chatbot/engine.py:246` |

#### Optional Variables

| Variable | Purpose | Default | Used In |
|----------|---------|---------|---------|
| `DEBUG` | Enable debug mode | `True` | `settings.py:29` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,0.0.0.0,testserver` | `settings.py:31` |
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.console.EmailBackend` | `settings.py:254` |
| `EMAIL_USE_TLS` | Enable TLS for SMTP | `True` | `settings.py:259` |
| `DEFAULT_FROM_EMAIL` | Default sender email | Auto-detected from `EMAIL_HOST_USER` | `settings.py:262-270` |
| `REDIS_AVAILABLE` | Enable Redis channel layer | `true` | `settings.py:107` |
| `FRONTEND_BASE_URL` | Frontend URL for email links | `http://localhost:5173` | `accounts/views.py:135`, `api/auth_password_views.py:59` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `''` | `settings.py:246` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `''` | `settings.py:247` |

**Note**: In production (Railway), database credentials are typically provided via Railway's environment variables, not `.env` file.

### Frontend Environment Variables

Frontend environment variables are loaded via Vite's `import.meta.env` and must be prefixed with `VITE_`.

| Variable | Purpose | Default | Used In |
|----------|---------|---------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` | `frontend/client/src/api/config.js:6` |
| `VITE_USE_BACKEND_API` | Enable backend API (vs mock data) | `false` | `frontend/client/src/components/MainChat.jsx:10`, `frontend/client/src/api/annotations.js:5`, `frontend/client/src/App.jsx:22` |

**Usage**: Create a `.env` file in the `frontend/` directory:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_BACKEND_API=true
```

## 5. Authentication system

GenScholar uses Django's session-based authentication with email/OTP verification for signup and optional Google OAuth login.

### Email/OTP Verification Flow

**Step 1: Request Email Verification** (`POST /api/auth/request-email-verification/`)
- User provides email address
- Backend generates 6-digit OTP and stores in `EmailOTP` model
- OTP sent via email (expires in 10 minutes)
- **File**: `backend/accounts/views.py:591-697`

**Step 2: Verify OTP** (`POST /api/auth/verify-otp/`)
- User submits email and 6-digit OTP
- Backend validates OTP and marks `EmailOTP.is_verified = True`
- **File**: `backend/accounts/views.py:733-791`

**Step 3: Signup** (`POST /api/auth/signup/`)
- User provides username, email (must match verified email), password, confirm_password
- Backend validates password strength (8-15 chars, uppercase, lowercase, number, special char, not equal to username)
- Creates `User` and marks email as verified in `allauth.account.models.EmailAddress`
- Auto-logs in user
- **File**: `backend/accounts/views.py:401-543`

### Login Flow

**Login Endpoint** (`POST /api/auth/login/`)
- Accepts `identifier` (username OR email) and `password`
- Uses custom `UsernameOrEmailBackend` to authenticate
- Creates Django session and returns user data
- **File**: `backend/accounts/views.py:362-398`
- **Backend**: `backend/accounts/auth_backends.py`

### Session/Cookie Behavior

- **Session Cookie**: `SESSION_COOKIE_SAMESITE='None'`, `SESSION_COOKIE_SECURE=True` (for cross-origin)
- **CSRF Cookie**: `CSRF_COOKIE_HTTPONLY=False` (so JavaScript can read it), `CSRF_COOKIE_SAMESITE='None'`, `CSRF_COOKIE_SECURE=True`
- **File**: `backend/genscholar/settings.py:307-317`

### Google Login

- Configured via `django-allauth` with Google provider
- Requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables
- OAuth URLs available at `/accounts/google/login/` (allauth default)
- **File**: `backend/genscholar/settings.py:236-251`

### CSRF Protection

**CSRF Token Endpoint** (`GET /api/auth/csrf/`)
- Returns CSRF token in JSON response and sets `csrftoken` cookie
- Frontend must include `X-CSRFToken` header in POST/PUT/PATCH/DELETE requests
- **File**: `backend/accounts/views.py:343-359`
- **Frontend**: `frontend/client/src/utils/csrf.js`, `frontend/client/src/api/client.js:22-38`

### Where Auth Logic Lives

- **Views**: `backend/accounts/views.py` (all auth endpoints)
- **Models**: `backend/accounts/models.py` (`PendingEmailVerification`, `EmailOTP`)
- **Backends**: `backend/accounts/auth_backends.py` (`UsernameOrEmailBackend`)
- **URLs**: `backend/genscholar/urls.py:21-32` (auth endpoints)
- **Settings**: `backend/genscholar/settings.py:208-233` (auth configuration)

## 6. API overview (important endpoints)

All API endpoints return JSON with `{"success": true/false, "data": {...}, "message": "..."}` format unless using DRF ViewSets (which return DRF format).

### Authentication Endpoints

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/auth/csrf/` | GET | Get CSRF token | None | `{success: true, data: {csrf_token: "..."}}` | `accounts/views.py:343` |
| `/api/auth/login/` | POST | Login user | `{identifier, password}` | `{success: true, data: {user: {id, username}}}` | `accounts/views.py:362` |
| `/api/auth/signup/` | POST | Create account | `{username, email, password, confirm_password}` | `{success: true, data: {user: {id, username}}}` | `accounts/views.py:401` |
| `/api/auth/logout/` | POST | Logout user | None | `{success: true, data: {message: "..."}}` | `accounts/views.py:546` |
| `/api/auth/user/` | GET | Get current user | None | `{success: true, data: {user: {id, username}}}` | `accounts/views.py:558` |
| `/api/auth/request-email-verification/` | POST | Send OTP email | `{email}` | `{success: true, data: {message: "..."}}` | `accounts/views.py:591` |
| `/api/auth/verify-otp/` | POST | Verify OTP | `{email, otp}` | `{success: true, data: {email, message}}` | `accounts/views.py:733` |
| `/api/auth/password-reset/` | POST | Request password reset | `{email}` | `{success: true, message: "..."}` | `api/auth_password_views.py:25` |
| `/api/auth/password-reset/confirm/` | POST | Confirm password reset | `{uid, token, new_password, re_new_password}` | `{success: true, message: "..."}` | `api/auth_password_views.py:123` |
| `/api/update-credentials` | POST | Update username/password | `{new_username?, new_password?}` | `{success: true, data: {message: "..."}}` | `accounts/views.py:846` |

### Workspace Endpoints

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/workspaces/` | GET | List user's workspaces | Query: `?q=search` | `{success: true, data: {workspaces: [...]}}` | `workspaces/views.py:220` |
| `/api/workspaces/` | POST | Create workspace | `{name}` | `{success: true, data: {workspace: {...}}}` | `workspaces/views.py:249` |
| `/api/workspaces/<id>/` | DELETE | Delete workspace | None | `{success: true, message: "..."}` | `workspaces/views.py:299` |
| `/api/workspaces/<id>/members/` | GET | List workspace members | None | `{success: true, data: {members: [...]}}` | `api/views.py:292` |
| `/api/workspaces/<id>/invite/` | POST | Invite user | `{username, role?}` | `{success: true}` | `api/views.py:490` |
| `/api/workspaces/<id>/members/<member_id>/` | PATCH | Change member role | `{role}` | `{success: true, data: {member: {...}}}` | `api/views.py:600` |
| `/api/workspaces/<id>/pinned-note/` | GET/POST/PUT/DELETE | Manage pinned note | `{content?}` | `{success: true, data: {...}}` | `api/views.py:397` |

### PDF Endpoints (DRF ViewSet)

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/pdfs/` | GET | List PDFs | Query: `?workspace=<id>` | DRF paginated list | `api/views.py:56` |
| `/api/pdfs/` | POST | Upload PDF | `FormData: {file, workspace, title}` | DRF object | `api/views.py:115` |
| `/api/pdfs/<id>/` | DELETE | Delete PDF | None | 204 No Content | `api/views.py:138` |
| `/api/pdfs/<id>/file/` | GET | Download PDF | None | `application/pdf` binary | `api/views.py:172` |

### Thread Endpoints (DRF ViewSet)

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/threads/` | GET | List threads | Query: `?workspace_id=<id>&pdf_id=<id>` | DRF list | `threads/views.py:75` |
| `/api/threads/` | POST | Create thread | `{workspace_id, pdf_id, page_number, selection_text, anchor_rect, anchor_side}` | DRF object | `threads/views.py:99` |
| `/api/threads/<id>/messages/` | POST | Add message to thread | `{content}` | DRF object | `threads/views.py:154` |
| `/api/threads/<id>/get_messages/` | GET | Get thread messages | None | DRF list | `threads/views.py:239` |

### Chat Endpoints (DRF ViewSet)

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/messages/` | GET | List chat messages | Query: `?workspace_id=<id>` | DRF list | `api/views.py:217` |
| `/api/messages/` | POST | Send chat message | `{workspace, message}` | DRF object | `api/views.py:229` |

### Chatbot Endpoints

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/chatbot/ask/` | POST | Ask AI question | `{question, workspace_id}` | `{status: "ok", user_question: "...", ai_answer: "..."}` | `chatbot/views.py:17` |

### Annotation Endpoints (DRF ViewSet)

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/annotations/` | GET | List annotations | Query: `?pdf_id=<id>` | DRF list | `api/views.py:199` |
| `/api/annotations/` | POST | Create annotation | `{pdf, page_number, coordinates, comment}` | DRF object | `api/views.py:211` |

### Notification Endpoints

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/notifications/` | GET | List notifications | None | `{success: true, data: {notifications: [...], unread_count: N}}` | `api/views.py:830` |
| `/api/notifications/<id>/` | PATCH | Mark as read | None | `{success: true, data: {message: "..."}}` | `api/views.py:884` |
| `/api/invitations/` | GET | List pending invitations | None | `{success: true, data: {invitations: [...]}}` | `api/views.py:676` |
| `/api/invitations/<id>/accept/` | POST | Accept invitation | None | `{success: true, data: {member: {...}}}` | `api/views.py:717` |
| `/api/invitations/<id>/decline/` | POST | Decline invitation | None | `{success: true, data: {message: "..."}}` | `api/views.py:790` |

### Profile Endpoints

| URL | Method | Purpose | Request | Response | File |
|-----|--------|---------|---------|----------|------|
| `/api/profile/me/` | GET | Get user profile with stats | None | `{success: true, data: {profile: {id, username, email, stats: {...}}}}` | `accounts/views.py:795` |

## 7. Realtime communication (Channels/WebSockets)

GenScholar uses Django Channels for WebSocket communication. The ASGI application routes WebSocket connections to consumers based on URL patterns.

### ASGI Configuration

**File**: `backend/genscholar/asgi.py`

The ASGI application routes:
- HTTP requests → Django ASGI app
- WebSocket requests → `AuthMiddlewareStack` → `URLRouter` → Consumer classes

### Channel Layer Configuration

**File**: `backend/genscholar/settings.py:103-144`

- **Production**: Redis channel layer (`channels_redis.core.RedisChannelLayer`) at `127.0.0.1:6379`
- **Development**: In-memory channel layer (`channels.layers.InMemoryChannelLayer`) if Redis unavailable
- Controlled by `REDIS_AVAILABLE` environment variable

### WebSocket Consumers

#### 1. Chat Consumer

**URL Pattern**: `ws/chat/<workspace_id>/`
**Group Name**: `workspace_{workspace_id}`
**File**: `backend/chat/consumer.py`

**Message Types:**
- **Incoming**: `{"message": "text"}` - User sends chat message
- **Outgoing**: `{"id": N, "message": "text", "username": "...", "timestamp": "..."}` - Broadcast to all members

**Behavior:**
- Checks workspace membership on connect
- Saves messages to `ChatMessage` model
- Detects `@mentions` and creates notifications
- Broadcasts to all workspace members

#### 2. Thread Consumer

**URL Pattern**: `ws/threads/workspace/<workspace_id>/pdf/<pdf_id>/`
**Group Name**: `threads_workspace_{workspace_id}_pdf_{pdf_id}`
**File**: `backend/threads/consumers.py`

**Message Types:**
- **Incoming**: None (threads created via HTTP API)
- **Outgoing**: 
  - `{"type": "thread.created", "thread": {...}}` - New thread created
  - `{"type": "message.created", "thread_id": N, "message": {...}}` - New message in thread

**Behavior:**
- Checks workspace membership on connect
- Receives broadcasts from `ThreadViewSet` when threads/messages are created via HTTP
- Broadcasts to all members viewing the same PDF

#### 3. Notification Consumer

**URL Pattern**: `ws/notifications/`
**Group Name**: `user_{user_id}`
**File**: `backend/notifications/consumer.py`

**Message Types:**
- **Incoming**: None
- **Outgoing**: `{"id": N, "message": "...", "created_at": "...", "unread_count": N}` - Notification data

**Behavior:**
- Each user connects to their personal notification channel
- Receives broadcasts when notifications are created (invitations, mentions, role changes, etc.)
- Used for real-time notification delivery

### Routing Files

- **Chat**: `backend/chat/routing.py`
- **Threads**: `backend/threads/routing.py`
- **Notifications**: `backend/notifications/routing.py`

All routing patterns are combined in `backend/genscholar/asgi.py:31`.

## 8. Notifications

GenScholar uses an in-app notification system with WebSocket delivery for real-time updates.

### Notification Model

**File**: `backend/workspaces/models.py:136-171`

**Fields:**
- `user` - Recipient user
- `type` - One of: `INVITATION`, `ROLE_CHANGED`, `MEMBER_ADDED`, `WORKSPACE_DELETED`, `MENTION`
- `title` - Notification title
- `message` - Notification message
- `related_workspace` - Optional workspace reference
- `related_invitation` - Optional invitation reference
- `is_read` - Read status
- `created_at` - Timestamp

### How Notifications Are Created

1. **Invitations**: Created when user invites another user to workspace (`api/views.py:565-589`)
2. **Mentions**: Created when `@username` is detected in chat messages or thread messages
   - Chat: `api/views.py:236-286`, `chat/consumer.py:102-151`
   - Threads: `threads/views.py:189-237`
3. **Role Changes**: Created when workspace creator changes member role (not currently implemented, but model supports it)
4. **Workspace Deleted**: Created when workspace is deleted (`workspaces/views.py:327-347`)

### How Users Receive Notifications

1. **WebSocket**: Real-time delivery via `NotificationConsumer` (group: `user_{user_id}`)
2. **REST API**: Polling via `GET /api/notifications/` endpoint
3. **Unread Count**: Included in WebSocket messages and API responses

### Relevant Endpoints/Consumers

- **GET** `/api/notifications/` - List all notifications with unread count
- **PATCH** `/api/notifications/<id>/` - Mark notification as read
- **WebSocket** `ws/notifications/` - Real-time notification delivery

## 9. Frontend structure

### API Client Configuration

**File**: `frontend/client/src/api/config.js`
- Exports `API_BASE_URL` from `VITE_API_BASE_URL` env var (default: `http://localhost:8000`)

**File**: `frontend/client/src/api/client.js`
- Core API client with CSRF token handling
- Functions: `apiRequest()`, `apiGet()`, `apiPost()`, `apiPut()`, `apiPatch()`, `apiDelete()`
- Automatically includes CSRF token in headers for state-changing requests
- Sets `credentials: 'include'` for cookie-based session auth

**API Module Files:**
- `frontend/client/src/api/auth.js` - Authentication functions
- `frontend/client/src/api/workspaces.js` - Workspace management
- `frontend/client/src/api/pdfs.js` - PDF upload/download
- `frontend/client/src/api/threads.js` - Thread management
- `frontend/client/src/api/chat.js` - Chat messages
- `frontend/client/src/api/chatbot.js` - AI chatbot
- `frontend/client/src/api/annotations.js` - PDF annotations
- `frontend/client/src/api/profile.js` - User profile
- `frontend/client/src/api/passwordReset.js` - Password reset

### Auth Pages

- **Login**: `frontend/client/src/routes/Login.jsx` (or similar)
- **Signup**: `frontend/client/src/routes/Signup.jsx` (or similar)
- **Email Verification**: `frontend/accounts/request_email_verification.html`, `frontend/accounts/email_verification_sent.html`

### WebSocket Clients

**File**: `frontend/client/src/utils/ws.js`
- WebSocket connection utilities for chat, threads, and notifications

### Project Structure

```
frontend/
├── client/
│   ├── src/
│   │   ├── api/          # API client modules
│   │   ├── components/   # React components
│   │   ├── routes/       # Route components
│   │   ├── utils/        # Utilities (CSRF, WebSocket, etc.)
│   │   ├── context/      # React context providers
│   │   └── hooks/         # Custom React hooks
│   └── index.html
├── package.json
└── vite.config.ts
```

## 10. Deployment details

### Production Stack

**Platform**: Railway (backend), Netlify (frontend)

**Backend Deployment**:
- **ASGI Server**: Gunicorn with Uvicorn workers (`gunicorn -k uvicorn.workers.UvicornWorker`)
- **Why ASGI + Gunicorn + Uvicorn**: 
  - Gunicorn is the process manager
  - Uvicorn workers handle ASGI protocol (needed for Channels/WebSockets)
  - Allows Django to serve both HTTP and WebSocket connections
- **Start Command**: `gunicorn -k uvicorn.workers.UvicornWorker genscholar.asgi:application --bind 0.0.0.0:$PORT`
- **File**: `railway.toml:10`, `backend/nixpacks.toml:11`

**Database**: PostgreSQL (provided by Railway)
- Connection via `DATABASES` setting using `POSTGRES_*` environment variables

**Redis**: Redis instance (for channel layer in production)
- Configured in `settings.py:109-121` to use Redis if available

**Static Files**: WhiteNoise middleware (`whitenoise==6.6.0`)
- Serves static files directly from Django (no separate static file server needed)

### CORS/CSRF Settings for Cross-Origin Deployment

**CORS Configuration** (`settings.py:284-299`):
- `CORS_ALLOWED_ORIGINS`: `["http://localhost:5173", "https://genscholar.netlify.app"]`
- `CORS_ALLOW_CREDENTIALS = True` - Allows cookies in cross-origin requests
- `CORS_ALLOW_ALL_HEADERS = True`
- `CORS_ALLOW_METHODS`: `["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]`

**CSRF Configuration** (`settings.py:301-313`):
- `CSRF_TRUSTED_ORIGINS`: `["http://localhost:5173", "https://genscholar.netlify.app"]`
- `CSRF_COOKIE_HTTPONLY = False` - JavaScript can read CSRF token
- `CSRF_COOKIE_SAMESITE = 'None'` - Allows cross-origin cookies
- `CSRF_COOKIE_SECURE = True` - Requires HTTPS in production

**Session Configuration** (`settings.py:315-317`):
- `SESSION_COOKIE_SAMESITE = 'None'` - Cross-origin session cookies
- `SESSION_COOKIE_SECURE = True` - HTTPS-only cookies

### Differences Between Local Dev and Production

1. **Database**: 
   - Local: SQLite (`db.sqlite3`) if `POSTGRES_*` vars not set
   - Production: PostgreSQL (Railway)

2. **Channel Layer**:
   - Local: In-memory fallback if Redis unavailable
   - Production: Redis (required for multi-worker deployments)

3. **Static Files**:
   - Local: Served by Django dev server
   - Production: WhiteNoise middleware

4. **Email Backend**:
   - Local: Console backend (prints to console)
   - Production: SMTP (Gmail)

5. **Debug Mode**:
   - Local: `DEBUG=True` (default)
   - Production: `DEBUG=False` (set via env var)

6. **Allowed Hosts**:
   - Local: `localhost,127.0.0.1`
   - Production: Railway domain + Netlify domain

### Background Tasks

**File**: `backend/pdfs/tasks.py`, `backend/pdfs/signals.py`

- PDF processing runs as background tasks via `django-background-tasks`
- When PDF is uploaded, `post_save` signal triggers `process_pdf_task()`
- Task calls `chatbot.engine.add_pdf_to_workspace_index()` to:
  1. Extract text from PDF using PDFPlumber
  2. Generate summary and abstract using Gemini LLM
  3. Create embeddings using Cohere
  4. Add to FAISS vector index
- **To run tasks**: `python manage.py process_tasks` (must be running in production)

### Environment-Specific Files

- `railway.toml` - Railway deployment configuration
- `backend/nixpacks.toml` - Nixpacks build configuration
- `.env` - Local development environment variables (not committed)

---

## Additional Notes

### PDF Storage

PDFs are stored as `BinaryField` in the database (not filesystem). This simplifies deployment but may impact performance for very large files. Vector indexes are stored in `media/vector_indexes/workspace_index_{id}/`.

### AI Chatbot Architecture

The chatbot uses a router pattern:
1. **Classifier** (Gemini) determines intent: `summary`, `abstract`, `pdf_question`, or `off_topic`
2. **Router** handles each intent:
   - `summary`/`abstract`: Returns pre-generated summary/abstract from PDF model
   - `pdf_question`: Uses RAG (Retrieval-Augmented Generation) with FAISS vector store
   - `off_topic`: Returns "I cannot find that information..."
3. **Embeddings**: Cohere `embed-english-v3.0`
4. **LLM**: Google Gemini `gemini-flash-latest`

### Workspace Roles

- **RESEARCHER**: Can upload PDFs, create threads, send chat messages, use AI chatbot, invite users
- **REVIEWER**: Can view PDFs, read threads, send chat messages (cannot create threads, upload PDFs, or use chatbot)

### Thread System

Threads are anchored to specific text selections in PDFs. Each thread has:
- `page_number` - PDF page
- `selection_text` - Selected text
- `anchor_rect` - Normalized coordinates (0-1) for positioning
- `anchor_side` - 'left' or 'right' for icon placement

Threads are created via HTTP API, but updates are broadcast via WebSocket for real-time collaboration.

