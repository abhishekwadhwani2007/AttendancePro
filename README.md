Markdown
# AttendancePro v2.0 📸

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge&logo=appveyor)
![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/status-stable-success?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

</div>

**AttendancePro** is a desktop application that uses computer vision to automate attendance. It scans faces via a webcam, verifies them against a registered database, and logs the entry—completely hands-free.

I originally built v1.0 during my 12th grade (Commerce + CS). Now, **v2.0** is a complete rewrite featuring a modern dark-mode UI, graphical reports, and a modular codebase.

## 📸 Interface Preview

### 📊 Dashboard
The central hub for analytics and quick stats.
![Dashboard](screenshots/dashboard.png)

### 👥 Student Management
Manage classes and register new students easily.
| **Class Management** | **Add New Student** |
|:---:|:---:|
| ![Class Management](screenshots/classmanagement.png) | ![Add Student](screenshots/addstudent.png) |

### 🤖 Face Recognition in Action
Real-time detection and training process.
| **Recording Face Data** | **Taking Attendance** |
|:---:|:---:|
| ![Recording Data](screenshots/recordingfacedata.png) | ![Taking Attendance](screenshots/attendance.png) |

## 👨‍💻 The Story Behind This
> *"My goal is to become an AI/ML Engineer. My strength is Computer Science and understanding the logic behind the magic."*

I actually started in the Commerce stream in 11th grade, but my curiosity for logic and code dragged me into the world of AI. I spent about **6 months** building this project from scratch to truly understand how OpenCV and databases interact. This project was my "playground" to learn Python, and now I'm taking that passion forward in my Integrated MSc in AI/ML.

## 🚀 What's New in v2.0?
The biggest change is the shift from a basic script to a professional software architecture:

* **Modern UI:** Replaced standard Tkinter with **CustomTkinter** for a clean, modern dark theme.
* **Visual Analytics:** Added **Matplotlib** graphs to track attendance trends over time.
* **No Setup DB:** Switched to **SQLite** so the app works instantly without installing a separate SQL server.
* **Modular Code:** Split the spaghetti code into `frontend.py`, `backend.py`, and `db_logic.py` for easier maintenance.

## 📂 Project Structure
```text
AttendancePro/
├── face_dataset/       # Stores numpy arrays of face embeddings
├── screenshots/        # Images for the README
├── backend.py          # Face recognition & logic
├── db_logic.py         # SQLite database operations
├── frontend.py         # CustomTkinter GUI
├── main.py             # Application entry point
├── haarcascade...xml   # OpenCV face detection model
└── requirements.txt    # Project dependencies
💡 Key Features
Face Recognition: Uses OpenCV (Haar Cascades + KNN) to identify students in real-time.

Voice Feedback: The system speaks back (via pyttsx3) to confirm when attendance is marked.

Smart Dashboard: View total students, present today, and attendance history at a glance.

Export Data: Download attendance logs as CSV files for Excel/Sheets.

🛠️ Tech Stack
Language: Python 3.x

GUI: CustomTkinter (Modern UI wrapper)

Computer Vision: OpenCV & NumPy

Database: SQLite (Built-in, lightweight)

Visualization: Matplotlib

⚡ How to Run
1. Clone the repo:

Bash
git clone [https://github.com/abhishekwadhwani2007/AttendancePro.git](https://github.com/abhishekwadhwani2007/AttendancePro.git)
cd AttendancePro
2. Install dependencies:

Bash
pip install -r requirements.txt
3. Run the app:

Bash
python main.py
Note: The database (attendance.db) will be created automatically on the first run.

Made with ❤️ by Abhishek Wadhwani