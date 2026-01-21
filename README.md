# Face Attendance System

This is the final practical project I built during my 12th grade (Commerce + Computer Science stream). I spent about **6 months** developing this from scratch to understand how computer vision and database management actually work together.

It’s not just a script—it’s a full desktop application that uses your webcam to mark attendance and saves it to a MySQL database.

## 👨‍💻 My Journey
> *"My goal is to become an AI/ML Engineer. My strength is Computer and Understanding the logic."*

I originally took Commerce in 11th grade, but my interest in logic and coding "dragged me" into the world of AI. This project was my playground to learn **Python, MySQL, and Logic Building**. Currently, I am taking this passion forward by pursuing an **Integrated MSc. in AIML**.

## 💡 What the Project Does
The system is designed to automate the old-school attendance process.
* **Scans Faces:** It uses OpenCV (Haar Cascades + KNN) to recognize registered students via webcam.
* **Talks Back:** I added a text-to-speech feature (`pyttsx3`) so the system verbally confirms when attendance is marked.
* **Alerts Parents:** If a student is marked present, it can trigger an SMS notification to their parents.
* **Saves Data:** All records (Name, Roll No, Time) are stored in a local MySQL database.
* **Export:** You can download the attendance report as a CSV file.

## 🛠️ How I Built It
* **Language:** Python
* **Interface:** Tkinter (I designed the GUI to be user-friendly with a blue theme).
* **Database:** MySQL (For storing student profiles and daily logs).
* **Libraries:** `opencv-python`, `numpy`, `mysql-connector`, `requests`.

## 🚀 How to Run It on Your PC

**1. Clone this repo**
```bash
git clone [https://github.com/yourusername/face-attendance-system.git](https://github.com/yourusername/face-attendance-system.git)
cd face-attendance-system

Install the libraries I have listed everything you need in requirements.txt
Using: pip install -r requirements.txt

