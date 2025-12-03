# Moodle BBB Notifier

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

A Python script to monitor **BigBlueButton (BBB) sessions** in Moodle and send **Discord notifications** before the sessions start. Ideal for students or teachers who want to get alerts for upcoming sessions automatically.

---

## Features

- Automatically fetches your enrolled Moodle courses.
- Finds BigBlueButton session links within courses.
- Parses French and ISO date formats for session schedules.
- Sends notifications to Discord **before sessions start**.
- Keeps track of notified sessions to prevent duplicates.

---

## Requirements

- Python 3.10 or higher
- Python packages:
pip install requests beautifulsoup4 python-dotenv


Installation & Setup Example


# Clone the repository
git clone https://github.com/OutOfAmine/discord-cours-notif.git
cd discord-cours-notif

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the project root with your credentials
echo "MOODLE_SESSION_TOKEN=your_moodle_session_cookie" >> .env
echo "MOODLE_ID1_TOKEN=your_moodle_id1_cookie" >> .env
echo "DISCORD_WEBHOOK_URL=your_discord_webhook_url" >> .env

# Run the script
python script.py


Configuration

| Variable            | Description                                               | Default             |
| ------------------- | --------------------------------------------------------- | ------------------- |
| `NOTIFY_BEFORE_MIN` | Minutes before session start to send Discord notification | 15                  |
| `COURSES_FILE`      | JSON file storing enrolled courses                        | `courses_list.json` |
| `BBB_HISTORY`       | JSON file storing notified sessions                       | `bbb_history.json`  |
| `TZ`                | Timezone for scheduling (Africa/Casablanca)               | `Africa/Casablanca` |


Environment Variables

| Variable               | Description                                  |
| ---------------------- | -------------------------------------------- |
| `MOODLE_SESSION_TOKEN` | Moodle session cookie (from browser)         |
| `MOODLE_ID1_TOKEN`     | Moodle user ID cookie (from browser)         |
| `DISCORD_WEBHOOK_URL`  | Discord webhook URL to receive notifications |



File Structure

.
├── script.py           # Main Python script
├── courses_list.json    # Stores fetched courses
├── bbb_history.json     # Stores notification history
├── .env                 # Environment variables (not committed)
└── README.md            # This file


Notes

Supports parsing dates in French formats (e.g., "15 janvier 2025 14:30") and ISO formats.

Keeps track of notified sessions to prevent duplicate notifications.

Can be customized for other time zones or notification timings.


Example Output

[OK] 5 courses saved -> courses_list.json
001. 101 - Mathématiques
002. 102 - Informatique
003. 103 - Physique

[NOTIF] Mathématiques @ 2025-12-03T14:30:00+01:00 -> True


License

MIT License


Author

Amine Jerrary - Full Stack Developer
