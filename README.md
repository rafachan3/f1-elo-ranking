# F1 Drivers ELO Rating 🏎️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Ff1-elo-ranking.onrender.com)](https://f1-elo-ranking.onrender.com/)

A comprehensive Formula 1 driver ranking system that uses ELO ratings to evaluate true driver ability by isolating car performance. Check out the live website: [F1 ELO Rankings](https://f1-elo-ranking.onrender.com/)

## 📖 Table of Contents
- [About](#about)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [Known Issues](#known-issues)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## About

Formula 1 is a sport where engineering plays a dominant role in performance. Teams with larger budgets can invest more in innovation, leading to better results. This makes it difficult to objectively determine the best driver, since car performance heavily influences race outcomes.

This project implements an ELO ranking system adapted for F1 to evaluate true driver ability. The ELO rating system, originally developed for chess, provides a mathematical method for calculating relative skill levels. In our F1 adaptation:

- Teammates drive identical cars, allowing direct performance comparisons
- Driver transitions between teams create a network of indirect comparisons
- Historical data from 1950 onwards is analyzed
- Results are adjusted for era-specific conditions and season lengths

## Features

- 📊 Comprehensive ELO rankings for all F1 drivers
- 📈 Detailed driver profiles with performance analytics
- 🔄 Head-to-head teammate comparisons
- 📅 Era-adjusted performance analysis
- 📱 Responsive web interface
- 🔍 Advanced filtering and search capabilities
- 📉 Interactive data visualizations
- 📧 Contact form for feedback and suggestions

## Getting Started

### Prerequisites

- Python 3.13.0
- Git
- VS Code (recommended)
- A Gmail account (for contact form functionality)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/f1-drivers-elo-ranking.git
cd f1-drivers-elo-ranking
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Environment Setup

1. Create a `.env` file in the root directory:
```env
FLASK_SECRET_KEY=your_generated_secret_key
MAIL_USERNAME=your_gmail_address
MAIL_PASSWORD=your_gmail_app_password
MAIL_RECIPIENT=your_recipient_email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

To generate a secure `FLASK_SECRET_KEY`:
```python
import secrets
secure_key = secrets.token_hex(32)
print(secure_key)
```

2. Gmail Setup:
   - Enable 2-factor authentication in your Google Account
   - Generate an App Password:
     1. Go to Google Account settings
     2. Navigate to Security
     3. Under "Signing in to Google," select App Passwords
     4. Generate a new app password for "Mail"
     5. Use this password as your `MAIL_PASSWORD`

## Usage

1. Start the development server:
```bash
python main.py
```

2. Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser

### VS Code Setup

1. Install recommended extensions:
   - Django (Baptiste Darthenay)
   - Python (Microsoft)
   - Pylance (Microsoft)
   - Python Debugger (Microsoft)

2. Configure Django HTML language mode:
   - Open any HTML file
   - Click on "Plain Text" in the bottom right corner
   - Select "Configure File Association for '.html'"
   - Choose "Django HTML"

3. Debug Configuration:
   1. Open the Debug view (Ctrl+Shift+D)
   2. Click "create a launch.json file"
   3. Select "Python"
   4. Choose "Flask"
   5. Update the configuration to:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### Troubleshooting

If you encounter "Access to 127.0.0.1 was denied" in Chrome:
1. Navigate to `chrome://net-internals/#sockets`
2. Click "Flush socket pools"
3. Refresh the development server

## Development

The project follows a specific commit message convention based on [Conventional Commits](https://www.conventionalcommits.org/):

1. Commits MUST be prefixed with a type: feat, fix, etc.
2. Use feat for new features
3. Use fix for bug fixes
4. Optional scope in parentheses
5. Description must follow the type/scope
6. Breaking changes must be indicated in footer
7. Example: `feat(database): add race count validation`

## Contributing

Contributions are welcome! We're looking for help with:
- Code improvements
- Bug fixes
- New features
- Documentation
- UI/UX enhancements

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'feat: Add AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## Roadmap

Planned features and improvements:

- Season-specific ELO progression viewer
- Constructor-based filtering and analysis
- Driver photos and nationality information
- Migration from CSV files to jolpica-f1 API integration
- Enhanced database architecture
- Improved visualization libraries
- Enhanced dashboard with more insights
- Automated data updates

## Known Issues

- ELO progression visualization issues for 1950s drivers
- Race count discrepancies for some drivers:
  - Bruce McLaren (+2 races)
  - Michael Schumacher (+2 races)
  - Richie Ginther (+1 race)
- Suboptimal "ELO Rating by Team" graph presentation
- Slower load times for individual driver profiles

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Data source: [Formula 1 World Championship (1950-2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) (CC0: Public Domain)

## Acknowledgments

- Inspired by [Mr V's Garage](https://www.youtube.com/watch?v=U16a8tdrbII) F1 ELO Engine video
- Thanks to the F1 community for continued support and feedback