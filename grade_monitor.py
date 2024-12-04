import asyncio
import json
import os
import time
from typing import Dict, List, Set, Optional
from datetime import datetime
from librus import Librus
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.librus_login = ""
        self.librus_password = ""
        self.gmail_address = ""
        self.gmail_app_password = ""  # App password, not your regular Gmail password
        self.notification_email = ""   # Where to send notifications
        self.check_interval = 300      # 5 minutes default

    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.librus_login = data.get('librus_login', '')
                    self.librus_password = data.get('librus_password', '')
                    self.gmail_address = data.get('gmail_address', '')
                    self.gmail_app_password = data.get('gmail_app_password', '')
                    self.notification_email = data.get('notification_email', '')
                    self.check_interval = data.get('check_interval', 300)
                return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
        return False

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'librus_login': self.librus_login,
                    'librus_password': self.librus_password,
                    'gmail_address': self.gmail_address,
                    'gmail_app_password': self.gmail_app_password,
                    'notification_email': self.notification_email,
                    'check_interval': self.check_interval
                }, f, indent=4)
            print("Configuration saved successfully")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
        return False

    def setup(self):
        """Interactive configuration setup"""
        print("\nLibrus Grade Monitor Configuration")
        print("---------------------------------")
        
        # Librus credentials
        self.librus_login = input("Enter your Librus login: ").strip()
        self.librus_password = input("Enter your Librus password: ").strip()
        
        # Gmail configuration
        print("\nGmail Configuration (for sending notifications)")
        print("Note: You need to use an App Password, not your regular Gmail password!")
        print("To create one, go to: Google Account -> Security -> 2-Step Verification -> App passwords")
        self.gmail_address = input("Enter your Gmail address: ").strip()
        self.gmail_app_password = input("Enter your Gmail App Password: ").strip()
        self.notification_email = input("Enter email where you want to receive notifications: ").strip()
        
        # Check interval
        try:
            interval = input("Enter check interval in minutes (default 5): ").strip()
            if interval:
                self.check_interval = int(interval) * 60
        except ValueError:
            print("Invalid interval, using default (5 minutes)")
            self.check_interval = 300
        
        return self.save()
# ... (previous Config class remains the same)

class GradeMonitor:
    def __init__(self):
        self.config = Config()
        self.known_grades: Set[int] = set()
        self.librus = Librus(None)
        self.api_data: Dict = {}
        self.subjects: Dict[int, str] = {}
        self.categories: Dict[int, Dict] = {}
        self.teachers: Dict[int, Dict] = {}

    def load_api_data(self):
        """Load API data from dump file"""
        try:
            with open('api_dump.json', 'r', encoding='utf-8') as f:
                self.api_data = json.load(f)
                
            # Extract subjects
            if 'Subjects' in self.api_data:
                for subject in self.api_data['Subjects'].get('Subjects', []):
                    self.subjects[subject['Id']] = subject['Name']
                    
            # Extract grade categories
            if 'Grades/Categories' in self.api_data:
                for category in self.api_data['Grades/Categories'].get('Categories', []):
                    self.categories[category['Id']] = {
                        'name': category['Name'],
                        'weight': category.get('Weight', 'none')
                    }
                    
            # Extract teachers
            if 'Users' in self.api_data:
                for user in self.api_data['Users'].get('Users', []):
                    self.teachers[user['Id']] = {
                        'first_name': user['FirstName'],
                        'last_name': user['LastName']
                    }
                    
            print("Successfully loaded API data")
        except FileNotFoundError:
            print("Warning: api_dump.json not found. Will use IDs instead of names.")
        except Exception as e:
            print(f"Error loading API data: {e}")

    def load_known_grades(self):
        """Load previously seen grades from file"""
        try:
            if os.path.exists('known_grades.json'):
                with open('known_grades.json', 'r') as f:
                    content = f.read().strip()
                    if content:  # Only try to parse if file is not empty
                        self.known_grades = set(json.loads(content))
                    else:
                        print("Known grades file is empty, starting fresh.")
                        self.known_grades = set()
            else:
                print("No previous grades file found, starting fresh.")
                self.known_grades = set()
        except json.JSONDecodeError:
            print("Error reading known grades file, starting fresh.")
            self.known_grades = set()
            # Remove corrupted file
            if os.path.exists('known_grades.json'):
                os.remove('known_grades.json')
        except Exception as e:
            print(f"Unexpected error loading known grades: {e}, starting fresh.")
            self.known_grades = set()
        
    def save_known_grades(self):
        """Save currently known grades to file"""
        try:
            with open('known_grades.json', 'w') as f:
                json.dump(list(self.known_grades), f)
        except Exception as e:
            print(f"Error saving known grades: {e}")

    def send_email(self, subject: str, content: str):
        """Send email notification using Gmail"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.gmail_address
            msg['To'] = self.config.notification_email
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'plain'))

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.config.gmail_address, self.config.gmail_app_password)
            server.send_message(msg)
            server.quit()
            print(f"Email notification sent to {self.config.notification_email}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def get_teacher_name(self, teacher_id: int) -> str:
        if teacher_id in self.teachers:
            teacher = self.teachers[teacher_id]
            return f"{teacher['first_name']} {teacher['last_name']}"
        return f"Teacher ID: {teacher_id}"

    def get_category_info(self, category_id: int) -> str:
        if category_id in self.categories:
            category = self.categories[category_id]
            weight = f" (weight: {category['weight']})" if category['weight'] != 'none' else ""
            return f"{category['name']}{weight}"
        return f"Category ID: {category_id}"

    def format_grade_info(self, grade: Dict) -> str:
        date = datetime.strptime(grade["AddDate"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
        subject_name = self.subjects.get(grade['Subject']['Id'], f"Subject ID: {grade['Subject']['Id']}")
        teacher_name = self.get_teacher_name(grade['AddedBy']['Id'])
        category_info = self.get_category_info(grade['Category']['Id'])
        
        grade_info = [
            f"New grade in {subject_name}",
            f"Grade: {grade['Grade']}",
            f"Category: {category_info}",
            f"Added by: {teacher_name}",
            f"Date: {date}"
        ]
        
        if grade['IsSemester'] or grade['IsSemesterProposition']:
            grade_info.append("Type: Semester grade")
        elif grade['IsFinal'] or grade['IsFinalProposition']:
            grade_info.append("Type: Final grade")
            
        if 'Improvement' in grade:
            grade_info.append("This is an improvement grade")
        if 'Resit' in grade:
            grade_info.append("This is a resit grade")
            
        return "\n".join(grade_info)

    async def get_current_grades(self) -> List[Dict]:
        try:
            response = await self.librus.get_data("Grades")
            if response and "Grades" in response:
                return response["Grades"]
        except Exception as e:
            print(f"Error fetching grades: {e}")
        return []

    async def check_for_updates(self):
        current_grades = await self.get_current_grades()
        
        for grade in current_grades:
            grade_id = grade["Id"]
            if grade_id not in self.known_grades:
                grade_info = self.format_grade_info(grade)
                print("\nNEW GRADE DETECTED!")
                print("-" * 50)
                print(grade_info)
                if "Comments" in grade:
                    print("This grade has a comment attached")
                print("-" * 50)
                
                # Send email notification
                subject_name = self.subjects.get(grade['Subject']['Id'], f"Subject ID: {grade['Subject']['Id']}")
                self.send_email(
                    f"New Grade in {subject_name}",
                    grade_info + "\n\nThis notification was sent by Librus Grade Monitor"
                )
                
                self.known_grades.add(grade_id)
        
        self.save_known_grades()

    async def run(self):
        print("Starting Librus grade monitor...")
        
        # Load or setup configuration
        if not self.config.load():
            if not self.config.setup():
                print("Failed to setup configuration!")
                return
        
        self.load_api_data()
        
        # Use credentials from config
        if not await self.librus.mktoken(self.config.librus_login, self.config.librus_password):
            print("Authentication failed!")
            return

        print(f"\nSuccessfully authenticated. Checking for updates every {self.config.check_interval} seconds...")
        print("Press Ctrl+C to stop")
        
        # Test email
        self.send_email("Grade Monitor Started", 
                       "The Librus grade monitoring service is now active")
        
        self.load_known_grades()
        
        while True:
            try:
                await self.check_for_updates()
                await asyncio.sleep(self.config.check_interval)
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                self.send_email("Grade Monitor Stopped", 
                              "The Librus grade monitoring service has been stopped")
                break
            except Exception as e:
                print(f"Error occurred: {e}")
                await asyncio.sleep(self.config.check_interval)

if __name__ == "__main__":
    monitor = GradeMonitor()
    asyncio.run(monitor.run())