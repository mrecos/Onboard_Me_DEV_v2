# Financial Legacy Account Assistant

## Overview
The Financial Legacy Account Assistant is a Flask-based backend application that analyzes financial transaction data using Large Language Models (LLM) to identify and track significant financial accounts. The system is designed to help users understand their financial footprint and identify important accounts that would be relevant for estate planning or financial management purposes.

## Architecture

### Core Components
The application is structured into three main components:

1. **Core Module** (`core.py`)
   - Contains fundamental services and shared functionality
   - Manages global state and configurations
   - Handles database connections and LLM initialization
   - Provides core utilities used throughout the application

2. **API Endpoints** (`templates/api/v1/endpoints.py`)
   - Implements versioned REST API endpoints
   - Processes incoming requests and manages responses
   - Coordinates between the frontend and core services

3. **Application Configuration** (`application.py`)
   - Initializes the Flask application
   - Registers blueprints and routes
   - Manages application-level settings

### Database Integration
The application integrates with a PostgreSQL database hosted on AWS RDS to store and manage:
- User transaction data
- Account tracking information
- Analysis results

### LLM Integration
The system leverages OpenAI's GPT-4 model through the LangChain framework to:
- Analyze financial transactions
- Identify significant financial relationships
- Generate structured insights about user accounts

## Key Features

### Transaction Analysis
- Processes user financial transaction data
- Identifies important financial accounts and relationships
- Categorizes transactions with confidence ratings
- Maintains historical tracking of account status

### Monitoring Interface
The application includes a dedicated monitoring dashboard (`monitor.html`) that provides:
- Real-time log viewing
- LLM output history
- System health monitoring
- Testing controls for API endpoints

### API Versioning
The API is versioned to ensure backward compatibility and smooth updates:
- All endpoints are prefixed with version information (e.g., `/api/v1/`)
- Different versions can coexist to support gradual migration
- Clear separation between API versions for maintenance

## Main Functions

### Database Operations
```python
get_db_connection()
```
Establishes and manages PostgreSQL database connections with proper configuration and error handling.

### LLM Processing

```python
convo_interpretor(init_user_prompt, chunks=None, instructions=None)
```
Processes user transaction data through the LLM to generate insights and identify important accounts.

### Logging and Monitoring
```python
add_log(message)
```
Maintains system logs with timestamps for monitoring and debugging purposes.

### Setup and Deployment
#### Prerequisites

- Python 3.12 or higher
- PostgreSQL database
- OpenAI API access
- AWS account for deployment

#### Local Development

- Clone the repository
- Install required dependencies: `pip install -r requirements.txt`
- Configure database credentials and OpenAI API key
- Run with Gunicorn: `gunicorn application:app`

#### Production Deployment
The application is designed for deployment on AWS Elastic Beanstalk with the following considerations:

- Uses Gunicorn as the WSGI HTTP Server
- Configured for high availability and scalability
- Includes proper error handling and logging
- Integrates with AWS RDS for database management

