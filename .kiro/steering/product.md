# Product Overview

Mojo is a personal automation and productivity platform built by Yehui Zhang. It provides:

- **FastAPI Service**: RESTful API at api.yehuizhang.com for personal tools and integrations
- **Telegram Bot (Chronos)**: Mobile-first interface for quick interactions and notifications
- **Task Scheduler**: Background automation for Gmail, DNS updates, and periodic jobs
- **Service Integration Hub**: Connects AWS, Google APIs, weather services, and other external APIs

## Problems It Solves

1. **Personal API Access**: Provides a unified API endpoint for personal tools
2. **Mobile Automation**: Telegram bot enables quick interactions and notifications on mobile
3. **Service Integration**: Connects various external services (AWS, Google, weather APIs) in one place
4. **Location Tracking**: Enables "whereis" functionality for location awareness
5. **Secure Access**: Invitation-code system ensures only trusted users can access services
6. **Multi-language Support**: Telegram bot supports multiple languages with translation files
7. **Logging & Monitoring**: Comprehensive ELK stack for activity tracking and debugging

## Core Features

- Invitation-only access with secure authentication
- Multi-language Telegram bot with user management
- Location tracking and "whereis" functionality
- Comprehensive logging and monitoring with ELK stack
- Redis caching for performance
- Docker-based deployment with environment separation (DEV/PROD)

## Target Users

Personal use system with invitation-code access for trusted users. Designed for mobile-first interactions through
Telegram while providing programmatic access via REST API.

## User Experience Goals

1. **Simple Access**: Single API endpoint for all personal tools
2. **Mobile-First**: Telegram bot as primary mobile interface
3. **Secure by Default**: Invitation-only access with proper authentication
4. **Multi-language**: Support for different languages in bot interactions
5. **Reliable**: High availability with proper error handling and logging
6. **Fast**: Quick response times with Redis caching
7. **Maintainable**: Clean code with pre-commit hooks and testing

## Key User Flows

1. **New User Onboarding**: Receive invitation code → Start bot → Select language → Access features
2. **API Access**: Authenticate with Bearer token → Access personal endpoints
3. **Location Tracking**: Send /whereis command → Receive last known location
4. **Service Monitoring**: Health checks → Log analysis via Kibana → Alert notifications

## Service Architecture

### API Service (FastAPI)

- RESTful API with Bearer token authentication
- Personal endpoints for various productivity tools
- Health checks and monitoring endpoints
- CORS configuration for web access
- Process time tracking middleware

### Telegram Bot (Chronos)

- Language selection on first use (/start command)
- Invitation code verification for new users
- Location tracking commands (/whereis)
- Help system (/help) showing available commands
- User scope and permission management
- Logging of user interactions

### Scheduler Service

- Background task execution
- Integration with Gmail API
- Periodic job scheduling
- DNS update automation

### Infrastructure

- Docker Compose orchestration
- Redis for caching and session management
- ELK stack for centralized logging and monitoring
- Environment-based configuration (DEV/PROD)
- AWS CDK for cloud infrastructure
- Automated builds and deployments