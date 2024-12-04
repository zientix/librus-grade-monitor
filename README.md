# Librus Grade Monitor

A Python-based monitoring system for Librus Synergia that tracks your grades and sends email notifications for new entries. This project is based on the [librusik](https://github.com/dani3l0/librusik) API wrapper.

## Features

- Real-time grade monitoring
- Email notifications for new grades
- Detailed grade information including:
  - Subject name
  - Grade value
  - Category and weight
  - Teacher name
  - Date and time
- Persistent grade tracking
- Configurable check intervals
- Easy setup with saved configuration

## Requirements

- Python 3.8+
- Gmail account with App Password enabled
- Librus Synergia account
- Required Python packages:
  ```
  aiohttp
  beautifulsoup4
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/librus-grade-monitor
   cd librus-grade-monitor
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

1. First, dump the API data to get subject and teacher information:
   ```bash
   python librus_api_dump.py
   ```

2. Configure the grade monitor by running:
   ```bash
   python grade_monitor.py
   ```
   
3. You will be prompted to enter:
   - Librus login credentials
   - Gmail address
   - Gmail App Password
   - Notification email address
   - Check interval (in minutes)

The configuration will be saved for future use.

## Gmail App Password Setup

1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled
4. Go to App Passwords
5. Create a new app password for "Mail"
6. Use this password in the grade monitor configuration

## Configuration Files

- `config.json`: Stores your login credentials and email settings
- `known_grades.json`: Keeps track of previously seen grades
- `api_dump.json`: Contains subject, teacher, and category information

## Project Structure

```
librus-grade-monitor/
├── librus.py           # Librus API wrapper (from librusik)
├── librus_api_dump.py       # API data dumping tool
├── grade_monitor.py    # Main monitoring script
├── config.json         # Configuration file
├── known_grades.json   # Grade tracking file
└── api_dump.json       # API data dump
```

## Credits

- Original Librus API wrapper: [librusik](https://github.com/dani3l0/librusik) by [dani3l0](https://github.com/dani3l0)
- `librus.py` and `librus_api_dump.py` are modified versions of code from the librusik project

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is not affiliated with, maintained, authorized, endorsed, or sponsored by Librus or any of its affiliates.  
it is also heavily created by a large language model, including this readme.
