# 💰 SmartExpense

A modern, web-based expense tracking application built with Flask. SmartExpense helps you manage personal finances with intuitive categorization, budgeting, and reporting features.

## ✨ Features

- **User Authentication**: Secure registration and login system
- **Expense Management**: Add, categorize, and track daily expenses
- **Budget Planning**: Set and monitor budgets by category
- **Interactive Dashboard**: Visual overview of spending patterns
- **Category Management**: Customizable expense categories
- **Data Export**: Export reports as CSV and PDF
- **Responsive Design**: Clean, mobile-friendly interface

## 🛠️ Tech Stack

- **Backend**: Flask 3.0+ with SQLAlchemy
- **Database**: SQLite (MVP) - Easily switchable to PostgreSQL/MySQL
- **Authentication**: Flask-Login
- **Frontend**: Jinja2 templates with modern CSS
- **Reporting**: ReportLab for PDF generation

## 📋 Prerequisites

- Python 3.10 or higher
- Windows PowerShell (or any terminal)

## 🚀 Quick Start

### 1. Clone and Setup Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# For Command Prompt/WSL:
# .venv\Scripts\activate.bat
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and update as needed:

```bash
cp .env.example .env
```

Edit `.env` with your preferences:
```env
SECRET_KEY=change-this-to-a-secure-random-string
DATABASE_URL=sqlite:///smartexpense.db
```

### 4. Run the Application

```bash
python wsgi.py
```

Open your browser and navigate to **http://127.0.0.1:5000/**

## 📖 User Guide

### First-Time Setup

1. **Create Account**: Visit `/auth/register` to register
2. **Login**: Access your account at `/auth/login`
3. **Setup Categories**: Add custom expense categories at `/expenses/categories`
4. **Add Expenses**: Start tracking expenses at `/expenses/`
5. **Set Budgets**: Define spending limits at `/budgets/`
6. **View Dashboard**: Monitor your finances at `/dashboard/`
7. **Generate Reports**: Export data at `/reports/`

### Key Features

- **Dashboard**: Real-time spending insights and budget status
- **Expense Tracking**: Quick expense entry with categorization
- **Budget Management**: Set monthly budgets and get alerts
- **Reports**: Generate CSV and PDF reports for analysis
- **Category Management**: Organize expenses with custom categories

## 📁 Project Structure

```
Internal-hackathon/
├── wsgi.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── .env.example           # Environment template
├── smartexpense/          # Main application package
│   ├── __init__.py        # App factory and initialization
│   ├── config.py          # Configuration settings
│   ├── extensions.py      # Flask extensions
│   ├── models/            # Database models
│   ├── blueprints/        # Route blueprints
│   ├── templates/         # Jinja2 templates
│   └── static/           # CSS, JS, and static assets
└── instance/             # Instance-specific files (database)
```

## 🔧 Configuration

### Database Setup

The application uses SQLite by default for simplicity. To switch to PostgreSQL or MySQL:

```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost/dbname

# MySQL
DATABASE_URL=mysql://username:password@localhost/dbname
```

### Security

- Change the `SECRET_KEY` in production
- Use HTTPS in production environments
- Consider adding CSRF protection for enhanced security

## 🚀 Deployment

### Production Setup

1. Set production environment variables
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure a reverse proxy (Nginx)
4. Set up proper database with migrations

```bash
# Example with Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Development Notes

- Database tables are created automatically on first run
- Default expense categories are seeded automatically
- Flask-Migrate is included for future database schema changes
- The application runs in debug mode by default in development

## 🔮 Future Enhancements

- [ ] Multi-currency support
- [ ] Recurring expenses
- [ ] Advanced analytics and charts
- [ ] Mobile app companion
- [ ] Bank account integration
- [ ] Team/family expense sharing

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues:

1. Check the existing documentation
2. Review the troubleshooting section
3. Open an issue on GitHub
4. Contact the development team

---

**Built with ❤️ for the Internal Hackathon**
