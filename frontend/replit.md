# GenScholar - Academic Research Tool

## Overview

GenScholar is a utility-focused academic research tool designed for extended PDF reading sessions with dark theme optimization. The application provides a collaborative workspace for managing research papers, annotations, and discussions. Built with a React frontend and Express backend, it emphasizes readability, minimal distractions, and zero animations for optimal focus during research work.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- **Framework**: React with TypeScript (using Vite as build tool)
- **UI Library**: Shadcn/ui components (Radix UI primitives)
- **Styling**: Tailwind CSS with custom dark theme design system
- **State Management**: TanStack Query (React Query) for server state
- **Form Handling**: React Hook Form with Zod validation

**Design Philosophy:**
- Dark-first theme optimized for extended reading sessions (#121212 background, #E0E0E0 text)
- 8px-based spacing system for consistent layout
- System font stack for performance and familiarity
- Utility-focused with zero animations to minimize distractions
- Mobile-responsive with breakpoint at 768px

**Component Structure:**
- Comprehensive UI component library in `client/src/components/ui/`
- Custom hooks for mobile detection and toast notifications
- Route-based architecture with Not Found fallback

### Backend Architecture

**Technology Stack:**
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js
- **Database ORM**: Drizzle ORM
- **Session Management**: Express sessions with PostgreSQL store (connect-pg-simple)
- **Build Tool**: esbuild for production builds

**Server Design:**
- RESTful API with `/api` prefix convention
- Request/response logging middleware for debugging
- Raw body buffering for webhook/payment integrations
- Vite development server integration with HMR
- Static file serving in production

**Storage Layer:**
- In-memory storage implementation (`MemStorage`) for development
- Interface-based design (`IStorage`) allows easy swapping to database
- Current schema supports user management with username/password authentication
- Ready for Drizzle ORM integration with PostgreSQL

### Data Storage Solutions

**Database Schema** (defined in `shared/schema.ts`):
- **Users Table**: ID (UUID), username (unique), password
- Drizzle ORM configured for PostgreSQL dialect
- Migrations stored in `./migrations` directory
- Zod schemas generated from Drizzle tables for validation

**Client-Side Storage** (localStorage):
- Authentication state (`gs_auth`)
- Workspaces collection (`gs_workspaces`)
- PDFs per workspace (`gs_pdfs::{workspaceId}`)
- Annotations per PDF (`gs_annotations::{workspaceId}::{pdfId}`)
- Discussion threads (`gs_threads::{workspaceId}::{pdfId}::{selectionId}`)
- Bot conversations and main chat per workspace

**PDF Processing:**
- PDF.js library for client-side PDF rendering and text extraction
- CDN-hosted worker for performance
- Text layer extraction for annotations and search

### Authentication and Authorization

**Current Implementation:**
- Username/password authentication schema defined
- Session-based authentication planned (connect-pg-simple configured)
- In-memory user storage for development
- Password hashing not yet implemented (should use bcrypt/argon2)

**Validation:**
- Yup schemas for login and account creation forms
- Email format validation
- Password minimum length (6 characters)
- Confirm password matching

### External Dependencies

**Core Libraries:**
- **@neondatabase/serverless**: PostgreSQL connection (serverless-compatible)
- **drizzle-orm**: Database ORM and query builder
- **drizzle-zod**: Automatic Zod schema generation from Drizzle tables
- **express**: Web server framework
- **vite**: Frontend build tool and dev server

**UI Component Libraries:**
- **@radix-ui/***: Accessible, unstyled UI primitives (20+ components)
- **tailwindcss**: Utility-first CSS framework
- **class-variance-authority**: Type-safe variant styling
- **lucide-react**: Icon library

**Form & Validation:**
- **react-hook-form**: Form state management
- **@hookform/resolvers**: Validation resolvers
- **zod**: Schema validation
- **yup**: Alternative validation (for legacy forms)

**Data Fetching:**
- **@tanstack/react-query**: Server state management, caching, and synchronization

**PDF Processing:**
- **pdfjs-dist**: PDF rendering and text extraction

**Development Tools:**
- **@replit/vite-plugin-***: Replit-specific development enhancements
- **tsx**: TypeScript execution for development server
- **esbuild**: Fast bundler for production builds

**Utilities:**
- **date-fns**: Date manipulation and formatting
- **uuid**: Unique ID generation
- **nanoid**: Short unique ID generation
- **clsx** & **tailwind-merge**: Conditional class name handling