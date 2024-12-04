import sys
import os
import asyncio
import json
from getpass import getpass as passw
from typing import Dict, Any, List, Optional

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from librus import Librus

KNOWN_ENDPOINTS = [
    "Me",
    "Schools",
    "Subjects",
    "Users",
    "Classes",
    "ClassFreeDays",
    "SchoolFreeDays",
    "TeacherFreeDays",
    "Grades",
    "Grades/Categories",
    "Grades/Comments",
    "BehaviourGrades",
    "Attendances",
    "Attendances/Types",
    "Lessons",
    "Timetables",
    "TimetableEntries",
    "HomeWorks",
    "HomeWorks/Categories",
    "LuckyNumbers",
    "ParentTeacherConferences",
    "UserProfile",
    "Virtual/StudentDirectoriesInWhichUserHasRights",
]

async def test_endpoint(librus: Librus, endpoint: str) -> Optional[Dict[str, Any]]:
    """Test a single endpoint and return the response data."""
    try:
        # Verify authentication
        me_data = await librus.get_data("Me")
        if not me_data:
            await librus.activate_api_access()
        
        # Make the request
        response = await librus.get_data(endpoint)
        return response
            
    except Exception:
        return None

async def dump_api(librus: Librus, endpoints: List[str], full_dump: bool = True, specific_path: str = None) -> Dict[str, Any]:
    result = {}
    
    # Verify API access
    if not await test_endpoint(librus, "Me"):
        if not await librus.activate_api_access():
            raise Exception("Could not activate API access")
    
    if full_dump:
        total = len(endpoints)
        for i, endpoint in enumerate(endpoints, 1):
            progress = round((i / total) * 100)
            print(f"[{str(progress).rjust(3)}%  {str(i).rjust(len(str(total)))}/{total}]  Requesting '{endpoint}'")
            
            response = await test_endpoint(librus, endpoint)
            result[endpoint] = response if response is not None else "Failed to fetch data"
            
            await asyncio.sleep(0.5)
    else:
        if specific_path not in endpoints:
            print(f"Warning: '{specific_path}' is not a known endpoint")
        
        response = await test_endpoint(librus, specific_path)
        if not response:
            print(f"Could not fetch data from {specific_path}")
            raise SystemExit(1)
            
        print(f"Successfully dumped '{specific_path}'")
        result[specific_path] = response
    
    return result

async def main():
    print("---------------- Librus API Dumper ----------------")

    _user = input("Librus Synergia login:        ")
    _pass = passw("Librus Synergia password:     ")
    _full_dump = input("Full API dump? [Y/n]:         ")
    
    _full_dump = _full_dump.strip().lower() not in ["n", "no", "false"]
    
    if _full_dump:
        print("Dumping full API...")
        _api_path = None
    else:
        _api_path = input("Enter API path to be dumped:  ").strip()
        print(f"Dumping only '{_api_path}' from API...")

    # Initialize Librus client
    librus = Librus(None)
    
    # Try authentication with retries
    for attempt in range(3):
        if await librus.mktoken(_user, _pass):
            print("Authentication successful")
            break
        print(f"Authentication attempt {attempt + 1} failed")
        if attempt < 2:
            print("Retrying authentication...")
            await asyncio.sleep(1)
    else:
        print("Authentication failed after 3 attempts")
        sys.exit(1)

    try:
        # Dump API data
        result = await dump_api(librus, KNOWN_ENDPOINTS, _full_dump, _api_path)

        # Save to file
        print("Saving data to JSON...")
        with open("api_dump.json", "w", encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print("Done.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())