import asyncio
import json
import os
from typing import Dict, List, Set
from datetime import datetime
import aiosmtplib  # Using aiosmtplib for async email sending
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from librus import Librus
from pathlib import Path
import logging
import sys

# This program automatically monitors your Librus grades and sends email notifications
# when new grades are added. It's made to work with Polish characters and has a nice
# email formatting. Just set it up once and forget about constantly checking Librus! 

class UTFStreamHandler(logging.StreamHandler):
    """
    Custom handler for console logging that properly handles Polish characters.
    Makes sure everything prints nicely in your terminal!
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.buffer.write(msg.encode('utf-8'))
            stream.buffer.write(self.terminator.encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

class UTFFileHandler(logging.FileHandler):
    """
    Custom handler for file logging that saves logs with Polish characters correctly.
    Your log files will be readable and won't have weird symbols!
    """
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)

# Setting up logging so we can see what's happening with our program
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        UTFStreamHandler(sys.stdout),
        UTFFileHandler('monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages all your settings like login, password, and email info.
    Saves everything securely in a config file so you don't have to
    type it in every time you run the program.
    """
    def __init__(self, config_path: str = 'config.json'):
        self.path = Path(config_path)
        self.config: Dict = {
            'librus_login': '',
            'librus_password': '',
            'gmail_address': '',
            'gmail_app_password': '',
            'notification_email': '',
            'check_interval': 300  # 5 minutes by default
        }

    def load(self) -> bool:
        """
        Loads your saved settings from the config file.
        Returns True if successful, False if something goes wrong.
        """
        try:
            if self.path.exists():
                self.config = json.loads(self.path.read_text(encoding='utf-8'))
                return True
            logger.warning("No configuration file found")
            return False
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def save(self) -> bool:
        """
        Saves your settings to the config file.
        Returns True if successful, False if something goes wrong.
        """
        try:
            self.path.write_text(
                json.dumps(self.config, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def setup(self) -> bool:
        """
        Walks you through setting up the program for the first time.
        Asks for your Librus login, Gmail info, and how often to check for grades.
        """
        print("\nLibrus Grade Monitor Configuration")
        print("-" * 35)
        
        try:
            self.config['librus_login'] = input("Librus login: ").strip()
            self.config['librus_password'] = input("Librus password: ").strip()
            
            print("\nEmail Configuration")
            print("Note: Use Gmail App Password, not regular password")
            print("Create one at: Google Account -> Security -> 2-Step Verification -> App passwords")
            
            self.config['gmail_address'] = input("Gmail address: ").strip()
            self.config['gmail_app_password'] = input("Gmail App Password: ").strip()
            self.config['notification_email'] = input("Notification email address: ").strip()
            
            interval = input("Check interval in minutes (default 5): ").strip()
            self.config['check_interval'] = int(interval) * 60 if interval else 300
            
            return self.save()
        except Exception as e:
            logger.error(f"Configuration setup failed: {e}")
            return False

class EmailSender:
    """
    Handles sending nice-looking email notifications about your new grades.
    Makes sure Polish characters show up correctly in emails!
    """
    def __init__(self, config: Dict):
        self.config = config

    async def send_email(self, subject: str, content: str) -> bool:
        """
        Sends an email with your grade info.
        Makes a pretty HTML version and a plain text version of the email.
        """
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.config['gmail_address']
            message['To'] = self.config['notification_email']
            message['Subject'] = subject

            # Making a nice-looking HTML email
            html_content = f"""
            <!DOCTYPE html>
            <html lang="pl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Jaro:opsz@6..72&display=swap');
                    body {{ font-family: Jaro, sans-serif; line-height: 1.6; }}
                    .grade-info {{  background: linear-gradient(to right, #8360c3, #2ebf91); font-size: 2.5em; padding: 15px; border-radius: 5px; color: #ffffff; }}
                </style>
            </head>
            <body>
                <div class="grade-info">
                    {content.replace('\n', '<br>')}
                </div>
            </body>
            </html>
            """

            message.attach(MIMEText(content, 'plain', 'utf-8'))
            message.attach(MIMEText(html_content, 'html', 'utf-8'))

            # Sending the email through Gmail
            await aiosmtplib.send(
                message,
                hostname="smtp.gmail.com",
                port=465,
                use_tls=True,
                username=self.config['gmail_address'],
                password=self.config['gmail_app_password']
            )
            
            logger.info(f"Email sent to {self.config['notification_email']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

class GradeTracker:
    """
    Keeps track of which grades we've already seen.
    This way you only get notifications for new grades!
    """
    def __init__(self, known_grades_path: str = 'known_grades.json'):
        self.path = Path(known_grades_path)
        self.known_grades: Set[int] = set()

    def load(self) -> None:
        """Loads the list of grades we've already notified you about"""
        try:
            if self.path.exists():
                content = self.path.read_text(encoding='utf-8').strip()
                if content:
                    self.known_grades = set(json.loads(content))
        except Exception as e:
            logger.error(f"Failed to load known grades: {e}")
            self.known_grades = set()

    def save(self) -> None:
        """Saves the list of grades we've seen so far"""
        try:
            self.path.write_text(
                json.dumps(list(self.known_grades), ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Failed to save known grades: {e}")

class LibrusMonitor:
    """
    The main part of the program that checks Librus for new grades
    and sends you notifications. It puts everything together!
    """
    def __init__(self):
        self.config_manager = ConfigManager()
        self.grade_tracker = GradeTracker()
        self.librus = Librus(None)
        self.email_sender = None
        self.api_data: Dict = {}

    def load_api_data(self) -> None:
        """
        Loads extra info about your subjects and teachers
        so notifications can show proper names instead of IDs
        """
        try:
            api_dump_path = Path('api_dump.json')
            if api_dump_path.exists():
                self.api_data = json.loads(api_dump_path.read_text(encoding='utf-8'))
                logger.info("API data loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load API data: {e}")
            self.api_data = {}

    def format_grade_info(self, grade: Dict) -> str:
        """
        Makes your grade notifications look nice and readable.
        Shows subject name, grade, category, teacher, and date.
        """
        try:
            date = datetime.strptime(grade["AddDate"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
            
            # Getting the subject name
            subject_id = grade['Subject']['Id']
            subjects_data = self.api_data.get('Subjects', {}).get('Subjects', [])
            subject_name = next(
                (s['Name'] for s in subjects_data if s['Id'] == subject_id),
                f"Subject ID: {subject_id}"
            )

            # Getting the teacher name
            teacher_id = grade['AddedBy']['Id']
            teacher = next(
                (u for u in self.api_data.get('Users', {}).get('Users', [])
                 if u['Id'] == teacher_id),
                {'FirstName': 'Unknown', 'LastName': f'Teacher (ID: {teacher_id})'}
            )
            
            # Getting the grade category and weight
            category_id = grade['Category']['Id']
            category = next(
                (c for c in self.api_data.get('Grades/Categories', {}).get('Categories', [])
                 if c['Id'] == category_id),
                {'Name': f'Category {category_id}', 'Weight': 'N/A'}
            )

            grade_info = [
                f"Przedmiot: {subject_name}",
                f"Ocena: {grade['Grade']}",
                f"Kategoria: {category['Name']} (waga: {category.get('Weight', 'N/A')})",
                f"Nauczyciel: {teacher['FirstName']} {teacher['LastName']}",
                f"Data: {date}"
            ]

            if grade.get('Comments'):
                grade_info.append("Komentarz dodany do oceny")

            return "\n".join(grade_info)
        except Exception as e:
            logger.error(f"Failed to format grade info: {e}")
            return str(grade)

    async def check_for_updates(self) -> None:
        """
        Checks Librus for new grades and sends you an email
        if there's anything new to report!
        """
        try:
            response = await self.librus.get_data("Grades")
            if not response or "Grades" not in response:
                return

            for grade in response["Grades"]:
                grade_id = grade["Id"]
                if grade_id not in self.grade_tracker.known_grades:
                    grade_info = self.format_grade_info(grade)
                    logger.info(f"New grade detected:\n{grade_info}")
                    
                    subject_id = grade['Subject']['Id']
                    subjects_data = self.api_data.get('Subjects', {}).get('Subjects', [])
                    subject_name = next(
                        (s['Name'] for s in subjects_data if s['Id'] == subject_id),
                        f"Subject {subject_id}"
                    )
                    
                    await self.email_sender.send_email(
                        f"Nowa ocena - {subject_name}",
                        grade_info
                    )
                    
                    self.grade_tracker.known_grades.add(grade_id)
                    self.grade_tracker.save()

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    async def run(self) -> None:
        """
        Starts up the monitor and keeps it running.
        This is what keeps checking for your grades!
        """
        logger.info("Starting Librus grade monitor...")

        # Load or setup configuration
        if not self.config_manager.load():
            if not self.config_manager.setup():
                logger.error("Failed to setup configuration!")
                return

        # Get everything ready
        self.email_sender = EmailSender(self.config_manager.config)
        self.load_api_data()
        self.grade_tracker.load()

        # Log into Librus
        if not await self.librus.mktoken(
            self.config_manager.config['librus_login'],
            self.config_manager.config['librus_password']
        ):
            logger.error("Authentication failed!")
            return

        logger.info(f"Monitor running. Checking every {self.config_manager.config['check_interval']} seconds")
        
        # Let you know the monitor started
        await self.email_sender.send_email(
            "Monitor Librus uruchomiony",
            "System monitorowania ocen został uruchomiony"
        )

        try:
            while True:
                await self.check_for_updates()
                await asyncio.sleep(self.config_manager.config['check_interval'])
        except KeyboardInterrupt:
            logger.info("Shutting down monitor...")
            await self.email_sender.send_email(
                "Monitor Librus zatrzymany",
                "System monitorowania ocen został zatrzymany"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    monitor = LibrusMonitor()
    asyncio.run(monitor.run())