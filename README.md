# GenScholar - Collaborative Research Paper Explorer

A collaborative research paper exploration platform that transforms PDF documents into interactive workspaces. Research teams can upload papers, generate AI-powered summaries, annotate text in real-time, hold threaded discussions on text selections, and chat with an AI assistant powered by the uploaded documents.

## Features

- **PDF Upload & Processing**: Upload research papers and extract text using AI
- **AI-Powered Summaries**: Generate intelligent summaries of research papers
- **Real-time Annotations**: Annotate and highlight text in documents
- **Threaded Discussions**: Hold context-aware discussions on specific text selections
- **AI Chat Assistant**: Chat with an AI assistant powered by your uploaded documents
- **Collaborative Workspaces**: Create and manage shared workspaces for research teams
- **Real-time Notifications**: Get notified about workspace activities and mentions

## Tech Stack

**Backend:**
- Django 5.2.7
- Django Channels (WebSocket support)
- PostgreSQL
- Redis
- LangChain (Google Gemini, Cohere embeddings)
- FAISS (Vector search)

**Frontend:**
- React 18
- Vite
- Wouter (Routing)
- React Query
- React PDF

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

## Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Test Users

**Note:** The create account feature is currently not working. Please use the following test accounts to access the platform:

| Username | Password | 
|----------|----------|
| `test1` | `Test@123` | 
| `test2` | `Test@123` | 
| `test3` | `Test@123` | 

## Design

**Figma Design Link:** https://www.figma.com/design/AAqZ7mNSsv7wgUD8Knafz8/Landingpage?node-id=0-1&p=f&t=6w8HarA02OcUARC5-0

## Team

| Sr. No. | Name               | ID         |
|--------:|-------------------|------------|
| 1       | Yug Savalia       | 202301263  |
| 2       | Archan Maru       | 202301217  |
| 3       | Dhruvil Patel     | 202301201  |
| 4       | Vedant Patel      | 202301227  |
| 5       | Manan Ghonia      | 202301240  |
| 6       | Dwarkesh Vaghasiya| 202301225  |
| 7       | Vatsal Somaliya   | 202301210  |
| 8       | Dhyey Raval       | 202301253  |
| 9       | Arav Vaitha       | 202301267  |
| 10      | Kanu Bhadraka     | 202301257  |

## Resources

- [Django Documentation](https://docs.djangoproject.com/en/5.2/)
- [React Documentation](https://react.dev/)
- [Django Channels Documentation](https://channels.readthedocs.io/)


