# Time Capsule 2.0

A social media platform where users can schedule posts that become visible only on the selected future date.

## Features
- User Registration & Login
- Create Scheduled Posts
- View Scheduled Posts upon Release Time
- MongoDB NoSQL Database
- Containerized with Docker & Docker Compose
- Automatic MongoDB Backup Restore

## Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MongoDB
- **Containerization:** Docker, Docker Compose

## How to Run Locally

### Prerequisites
- Docker & Docker Compose installed

### Clone the Repository
```bash
git clone https://github.com/YourUsername/TimeCapsule2.0.git
cd TimeCapsule2.0
```

### Build & Run Containers
```bash
docker-compose up --build
```

### Access the Application
Go to: [http://localhost:5000](http://localhost:5000)

## MongoDB Backup Restore
A backup of the initial database is available inside the `database/` directory as **backup.json**.

If you want to restore the backup manually:
1. Start the MongoDB container.
2. Run the following command inside the container:
```bash
docker exec -it <mongodb_container_name> mongorestore --jsonArray --db total_records /data/db/backup.json
```

## Environment Variables
Create a `.env` file with the following:
```env
SECRET_KEY=your_secret_key
MONGO_URI=mongodb://mongodb:27017/your_db_name
```

## Folder Structure
```
├── app.py             # Main Flask App
├── requirements.txt   # Python Dependencies
├── Dockerfile         # Backend Dockerfile
├── docker-compose.yml # Docker Compose Configuration
├── templates/         # HTML Templates
├── static/            # CSS, JS, Images
├── database/          # Backup Files
└── docker-data/       # MongoDB Volume Data
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE)

