A full-stack movie tracking and review platform inspired by Letterboxd.

Users can discover movies, rate them, write reviews, maintain watchlists, and interact with other users' activity.

**Live Demo:** [https://letterboxd-vp5a.onrender.com](https://letterboxd-vp5a.onrender.com)

---

## Features

- User authentication (Register / Login)
- Browse and search movies
- Rate movies (1–5 stars)
- Write and edit reviews
- Create and manage personal watchlist
- View other users' profiles and activity
- Responsive UI

## Tech Stack

### Backend
- **FastAPI**
- **PostgreSQL** + SQLAlchemy
- **Alembic** (migrations)
- **JWT Authentication** (python-jose + passlib)
- **Pydantic**

### Frontend
- **React** + Vite
- **Tailwind CSS**

### DevOps
- Docker + Docker Compose
- Deployed on Render

## Project Structure
Letterboxd/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── auth/         # Authentication logic
│   │   ├── crud/         # Database operations
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── db/           # Database session
│   ├── alembic/          # Database migrations
│   └── main.py
├── frontend/             # React + Vite application
├── docker-compose.yml
└── Dockerfile

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker (optional but recommended)

### 1. Clone the repository

```bash
git clone https://github.com/Devansh-debug344/Letterboxd.git
cd Letterboxd
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file and add your database URL + secret key
# Then run migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
Backend will run at: http://localhost:8000
Docs available at: http://localhost:8000/docs
cd frontend
npm install
npm run dev
docker-compose up --build

Method,Endpoint,Description
POST,/auth/register,Register new user
POST,/auth/login,Login and get JWT token
GET,/movies/,List / search movies
POST,/reviews/,Create a review
GET,/reviews/user/{id},Get reviews by user
POST,/watchlist/,Add movie to watchlist
GET,/watchlist/,Get current user's list

Future Improvements

 Social features (follow users, like reviews)
 Movie recommendations
 Better search with filters
 Image uploads for user profiles
 Improved mobile experience
 Caching layer (Redis)
