# CLAUDE.md

response in chinese

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **autoR** - a spaced repetition flashcard application (v2.0) for vocabulary learning based on the Ebbinghaus forgetting curve. The application implements the SM-2 algorithm for optimal review scheduling and supports both English words and Chinese characters (Hanzi).

**Architecture**: Modern SPA with separated frontend/backend
- **Backend**: Django 5 + Django REST Framework + SQLite
- **Frontend**: Vue 3 + Vite + Tailwind CSS + Pinia
- **Target**: Small user base (≤10 users), PWA-ready for offline usage

## Quick Start (一键启动)

### 🚀 最快启动方式

```bash
# 进入项目根目录
cd /home/momo/github_proj/autoR

# 一键启动（推荐）
./start.sh
```

**启动模式**:
1. **完整模式** - 前端 + 后端（tmux 分屏）
2. **仅后端** - Django API (端口 8000)
3. **仅前端** - Vue 3 (端口 5173)
4. **后台运行** - 不占用终端

**访问地址**:
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/api/
- Django 管理: http://localhost:8000/admin/

**停止服务**:
```bash
./stop.sh
```

**查看快速参考**:
```bash
./scripts/quick-ref.sh
```

详细说明请参考: `docs/启动指南.md`

---

## Development Commands

### Backend (Django)

All backend commands should be run from the `backend/` directory.

**快速启动（单独启动后端）**:
```bash
./scripts/start-backend.sh
```

**手动启动流程**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Database Operations**:
```bash
# Run migrations
python3 manage.py migrate

# Create superuser
python3 manage.py createsuperuser

# Import ECDICT dictionary (77万 English words)
python3 manage.py import_ecdict
```

**Development Server**:
```bash
# Run development server (port 8000)
python3 manage.py runserver

# Run with specific settings module if needed
DJANGO_SETTINGS_MODULE=config.settings python3 manage.py runserver
```

**Testing**:
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=cards --cov-report=html

# Run specific test file
pytest cards/test_sm2.py

# Run specific test module
pytest cards/tests.py -v
```

**Database Shell**:
```bash
# Django shell
python3 manage.py shell

# Database shell
python3 manage.py dbshell
```

### Frontend (Vue)

All frontend commands should be run from the `frontend/` directory.

**Installation**:
```bash
cd frontend
npm install
```

**Development**:
```bash
# Start dev server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Architecture & Key Modules

### Backend Structure

**Apps**:
- `cards/` - Main application containing all business logic

**Models** (`cards/models.py`):
- `Deck` - Card collections with daily limits configuration
- `Card` - Main flashcard entity with SM-2 algorithm fields (ef, interval, difficulty, stability)
- `ReviewLog` - Review history with before/after state snapshots for undo functionality
- `ECDict` - Read-only English dictionary (ECDICT) with 770K words

**Key Services** (`cards/services/`):
- `sm2.py` - Core SM-2 spaced repetition algorithm implementation
  - `process_review()` - Update card state based on quality rating (0=Again, 2=Hard, 4=Good, 5=Easy)
  - `generate_review_queue()` - Priority queue: due cards > leech cards (lapses≥3) > new cards
  - `calculate_ef()` - Calculate easiness factor using SM-2 formula
  - `undo_review()` - Restore card to previous state
- `baidu_hanyu.py` - Chinese character lookup service

**API Endpoints** (`cards/urls.py`):
- Authentication: `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/`
- Review session: `/api/review/queue/`, `/api/review/submit/`, `/api/review/undo/`
- Dictionary: `/api/dict/en/<word>/`, `/api/dict/zh/<char>/`, `/api/dict/zh/infer-pinyin/`
- CRUD: `/api/decks/`, `/api/cards/`, `/api/review-logs/` (DRF ViewSets)

### Frontend Structure

**Router** (`src/router/index.js`):
- `/` - Home dashboard
- `/login`, `/register` - Authentication
- `/review` - Review session interface
- `/cards`, `/cards/new` - Card management and creation
- `/stats` - Statistics and analytics

**Stores** (Pinia):
- `user.js` - User authentication state
- `review.js` - Review session state management

**Key Views**:
- `Review.vue` - Flashcard review interface with keyboard shortcuts
- `CardForm.vue` - Card creation with auto-complete from dictionary APIs
- `Stats.vue` - Learning statistics and progress visualization

### SM-2 Algorithm Implementation

The core review algorithm is in `backend/cards/services/sm2.py`:

**Learning Steps**:
- New cards: 10 minutes → 1 day → review
- Again (quality=0): restart from 10 minutes
- Graduate to review after completing learning steps

**Review Intervals**:
- First review: 1 day
- Second review: 6 days
- Subsequent: `interval × EF`

**Easiness Factor (EF)**:
- Initial: 2.5
- Range: [1.3, ∞]
- Formula: `EF' = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02))`

**Leech Detection**:
- Cards with `lapses ≥ 3` are marked as "leech" (difficult cards)
- Prioritized in review queue for extra practice

## Database Details

**Location**: `backend/db/db.sqlite3` (large file ~486MB due to ECDICT)

**Key Indexes** (for performance):
- Cards: Indexed on `(user, due_at)`, `(user, deck)`, `(user, state, due_at)`, `word`, `lapses`
- ReviewLog: Indexed on `(user, reviewed_at)`, `(card, reviewed_at)`
- ECDict: Indexed on `word`, `collins`, `oxford`

**Default Due Date**:
- New cards use `9999-12-31` as sentinel value (not yet in review queue)

## Configuration & Environment

**Backend Settings** (`backend/config/settings.py`):
- Environment variables supported: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`
- CORS enabled for development: `localhost:5173`, `127.0.0.1:5173`
- Session-based authentication (no token required)
- Rate limiting: 1000/hour for authenticated users, 100/hour for anonymous

**Frontend Configuration**:
- Vite dev server on port 5173
- Axios base URL points to `localhost:8000/api/`
- Path alias: `@` → `src/`

## Testing Strategy

**Backend Tests**:
- SM-2 algorithm tests: `backend/cards/test_sm2.py`
- API integration tests: `backend/test_dict_api.py`, `backend/test_bug_fixes.py`

**Coverage Requirements**:
- Default target: 85% (as per global AGENTS.md rules)
- Priority: SM-2 algorithm, API endpoints, data models

**Running Specific Tests**:
```bash
# Test SM-2 algorithm
cd backend
pytest cards/test_sm2.py -v

# Test dictionary API
pytest test_dict_api.py -v

# Test specific function
pytest cards/test_sm2.py::test_calculate_ef -v
```

## Data Sources & Auto-complete

**Four-layer fallback strategy** (L1 → L4):
1. **IndexedDB Cache** (frontend, not yet implemented in v2.0)
2. **Local ECDICT** (770K English words, imported to SQLite)
3. **Online APIs** (dictionaryapi.dev for English, Baidu Hanyu for Chinese)
4. **Manual Input** (fallback when all sources fail)

**Auto-complete Fields**:
- English: IPA, POS, meaning, examples, audio URL, CEFR level
- Chinese: Pinyin, variants, meaning, examples, radical, strokes

## Common Workflows

**Adding New Features**:
1. Backend: Create/modify models → migrations → serializers → views → URLs → tests
2. Frontend: Create/modify views → router → stores (if needed) → API calls

**Database Changes**:
```bash
cd backend
python3 manage.py makemigrations
python3 manage.py migrate
```

**Debugging**:
- Backend: Use `python3 manage.py shell` or add `import pdb; pdb.set_trace()`
- Frontend: Browser DevTools + Vue DevTools
- API: Django admin at `/admin/` or DRF browsable API

**Import/Export**:
- Cards support CSV/JSON export (future feature)
- ECDICT import: `python3 manage.py import_ecdict` (may take time for 770K records)

## Known Issues & Technical Debt

Based on git status:
- Modified files suggest ongoing work on:
  - SM-2 algorithm refinement (`cards/services/sm2.py`)
  - Card due date handling (`cards/models.py`)
  - Card form UI (`frontend/src/views/CardForm.vue`)
  - Settings configuration (`backend/config/settings.py`)

**PWA Features** (planned but not yet implemented):
- Service Worker for offline support
- IndexedDB caching layer (L1)
- Background sync for review data

## Security Notes

- **NEVER** commit `.env` files or expose `DJANGO_SECRET_KEY`
- Session cookies use `SameSite=Lax` for CSRF protection
- Rate limiting configured on authentication endpoints
- User data is isolated (all models filter by `user` foreign key)
- CORS restricted to specified origins (check `CORS_ALLOWED_ORIGINS`)

## Performance Considerations

- **Large database**: SQLite file is ~486MB due to ECDICT, ensure sufficient disk space
- **Query optimization**: Use `.select_related()` and `.prefetch_related()` for card queries
- **Review queue**: Limited to 50 cards by default to prevent memory issues
- **Frontend**: Code splitting via Vue Router lazy loading (`import('@/views/...')`)

## Dependencies

**Backend** (Python 3.10+):
- Django 5.0 + djangorestframework 3.16
- django-cors-headers, django-filter
- jieba, pypinyin (Chinese text processing)
- beautifulsoup4, requests (web scraping)
- pytest, pytest-django, pytest-cov (testing)

**Frontend** (Node.js):
- Vue 3.5 + vue-router + pinia
- axios (HTTP client)
- chart.js (statistics visualization)
- tailwindcss 3.4 (styling)
- vite 7.2 (build tool)
