# Upward Habits - Personal Habit Tracking Application

A comprehensive habit tracking application with advanced momentum scoring, WHOOP integration, and visual progress tracking.

## Features

- **Smart Habit Tracking**: Track four primary habit types (duration, pages, binary, inverted scoring)
- **Three-Tier Scoring**: Nonzero (0.3x), Goal (1.0x), and Stretch (1.5x) performance levels
- **Momentum System**: Rolling 7-day performance with compound growth and graduated decay
- **WHOOP Integration**: Biometric data integration with sleep, HRV, and recovery scoring
- **Visual Analytics**: Interactive charts and progress dashboards
- **Email Notifications**: Daily reminders with progress summaries
- **Mobile Responsive**: Optimized for both desktop and mobile use

## Tech Stack

- **Backend**: FastAPI with SQLModel and SQLite
- **Frontend**: Vue 3 with Chart.js for visualizations
- **Database**: SQLite (with Alembic migrations)
- **Deployment**: Single-process serving API + static frontend
- **Integrations**: WHOOP API, SMTP email notifications

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd upward
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   # Run migrations
   cd ..
   alembic upgrade head
   ```

5. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

6. **Build the frontend**
   ```bash
   npm run build
   ```

7. **Start the application**
   ```bash
   cd ../backend
   python -m app.main
   # Or with uvicorn
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

The application will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=sqlite:///./upward_habits.db

# WHOOP API (optional)
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_client_secret
WHOOP_REDIRECT_URI=http://localhost:8000/api/auth/whoop/callback

# Email notifications (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# App settings
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=True
TIMEZONE=America/Phoenix
```

### Default Habits

The application comes with four pre-configured habits:

1. **Reading** (Pages): Goal 3 pages, Stretch 5 pages
2. **Breathwork** (Duration): Goal 10 minutes, Stretch 20 minutes  
3. **Activity** (Binary): Goal completion, 4 days/week target
4. **Screen Time Post 9PM** (Inverted Duration): Goal <30min, Stretch 0min

Habits can be customized through the API or by modifying `backend/config/habits.json`.

## API Documentation

Once running, visit `http://localhost:8000/docs` for the interactive API documentation.

### Key Endpoints

- `GET /api/habits/` - List all habits
- `POST /api/habits/entries` - Submit daily habit data
- `GET /api/scores/daily` - Get daily scores time series
- `GET /api/scores/summary` - Current progress summary
- `POST /api/whoop/sync` - Sync WHOOP data

## Usage

### Daily Habit Entry

1. Navigate to the main page
2. Select the date (defaults to today)
3. Enter values for each habit
4. View real-time score calculation and weekly progress
5. Save all entries

### Progress Visualization

- **Progress Tab**: Line charts showing daily/cumulative scores
- **Weekly Tab**: 7-day rolling progress with momentum indicators
- Toggle between different views and time ranges
- Individual habit performance tracking

### WHOOP Integration

1. Click "Connect WHOOP" in the top-right
2. Complete OAuth authorization
3. Data will sync automatically
4. WHOOP scores influence daily multipliers

## Scoring Algorithm

### Base Scoring

Each habit gets scored based on performance tiers:
- **0.0**: No activity
- **0.3**: Nonzero threshold met
- **1.0**: Goal threshold met
- **1.5**: Stretch threshold exceeded

### Momentum Multiplier

Rolling 7-day performance determines momentum:
- **Exceed Target**: Compound growth (1.15x multiplier)
- **Meet Target**: Maintain momentum (1.0x)
- **Close to Target**: Gradual decay (0.9x)
- **Miss Target**: Faster decay (0.81x)
- **Complete Miss**: Rapid decay (0.73x)

### WHOOP Multiplier

Average of sleep, HRV, and recovery scores:
- Linear scaling around 70% baseline
- Range: 0.5x to 2.0x multiplier
- Applied to final daily score

### Final Score Calculation

```
Final Habit Score = Raw Score × Momentum Multiplier
Daily Score = Σ(Final Habit Score × Weight) / Σ(Weight)
Final Daily Score = Daily Score × WHOOP Multiplier
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

The frontend dev server will proxy API requests to the backend.

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend  
npm run test
```

## Deployment

### Single Server Deployment

The application is designed for single-process deployment:

1. Build the frontend: `cd frontend && npm run build`
2. The built files are served from `backend/static/`
3. Run with: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Production Settings

- Set `DEBUG=False` in environment
- Use a strong `SECRET_KEY`
- Consider PostgreSQL for production database
- Set up reverse proxy (nginx) for static files
- Configure SSL/TLS certificates

### Email Notifications

To enable daily email reminders:

1. Configure SMTP settings in `.env`
2. Set up a cron job to call the notification endpoint
3. Example cron entry for 8:45 AM daily:
   ```bash
   45 8 * * * curl -X POST http://localhost:8000/api/notifications/daily
   ```

## WHOOP Integration Setup

1. Register at [WHOOP Developer Portal](https://developer.whoop.com)
2. Create a new application
3. Set redirect URI to `http://localhost:8000/api/auth/whoop/callback`
4. Copy Client ID and Secret to `.env`
5. Required scopes: `read:recovery read:sleep read:measurement`

## Troubleshooting

### Common Issues

**Database not initialized**
```bash
alembic upgrade head
```

**WHOOP connection fails**
- Verify client ID and secret in `.env`
- Check redirect URI matches exactly
- Ensure WHOOP app has correct scopes

**Email notifications not working**
- Verify SMTP settings
- For Gmail, use App Password instead of regular password
- Check firewall/network restrictions

**Frontend not loading**
```bash
cd frontend
npm run build
```

### Logs

Application logs are written to stdout. For production, redirect to files:

```bash
uvicorn app.main:app --log-config logging.conf >> app.log 2>&1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Additional integrations (Oura, Fitbit, Apple Health)
- [ ] Social features and sharing
- [ ] Advanced analytics and insights
- [ ] Habit recommendation engine
- [ ] Export data functionality
- [ ] Multi-user support and teams