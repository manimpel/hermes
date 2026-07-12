# Hermes — AI-Powered Freelance Matchmaking Platform

Swipe-based freelancer matching powered by Claude AI.

## Stack
- **Frontend:** Next.js 14 + Tailwind + Framer Motion
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **AI:** Claude API (semantic matching, LinkedIn parsing)

## Setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your env vars
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

## Admin
- View pending OTPs: `GET /admin/otps` (Bearer hermes-admin-secret)
- Confirm payment: `POST /webhooks/confirm-payment/{project_id}?payment_type=ADVANCE`
- View users: `GET /admin/users`
