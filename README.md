🚨 RescueMesh

AI-Powered Emergency Rescue and Drone Coordination System

RescueMesh is a prototype designed to support emergency response by combining AI-based victim detection, drone coordination, and a live map dashboard.

🌟 Features

- AI-Based Victim Detection: Detects people using a camera and a YOLO-based model.
- Emergency Registration: Records emergency type and location.
- Drone Management: Tracks drone locations, battery levels, and availability.
- Rescue Recommendations: Suggests a drone or rescue resource based on available information.
- Drone Mission Simulation: Simulates drone movement toward a target location.
- Live Map Dashboard: Displays drones, detected victims, and emergencies.
- FastAPI Backend: Provides API endpoints for communication between the frontend and backend.

🛠️ Technology Stack

- Python
- FastAPI
- JavaScript, HTML, CSS
- YOLO / Ultralytics
- OpenCV
- Leaflet.js
- Git and GitHub

📁 Project Structure

RescueMesh/
├── ai_detection/
│   └── detect_victim.py
├── backend/
│   ├── main.py
│   ├── drone_manager.py
│   ├── drone_simulation.py
│   └── rescue_engine.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── .gitignore

⚙️ Setup and Installation

1. Clone the repository

git clone https://github.com/Rajivkumar-ray/RescueMesh.git
cd RescueMesh

2. Create and activate a virtual environment

Windows PowerShell:

python -m venv venv
.\venv\Scripts\Activate.ps1

3. Install backend dependencies

pip install fastapi uvicorn

Install any additional dependencies required by the project files.

4. Run the backend

cd backend
python -m uvicorn main:app --reload

Open the API documentation:

http://127.0.0.1:8000/docs

5. Run the frontend

Open "frontend/index.html" using the VS Code Live Server extension.

If the frontend is configured for "http://127.0.0.1:5500", use that address to access the dashboard.

🧪 Project Status

Prototype under development.

The project includes AI-based victim detection, emergency registration, drone management, rescue recommendations, and simulated drone movement.

Actual drone flight, field deployment, and real-world rescue operations require additional hardware integration, testing, and safety validation.

🔮 Future Improvements

- Persistent database integration
- Real-time GPS and telemetry
- Physical drone integration
- Improved emergency notifications
- More robust AI detection and validation

👨‍💻 Author

Rajiv Kumar

GitHub: https://github.com/Rajivkumar-ray
