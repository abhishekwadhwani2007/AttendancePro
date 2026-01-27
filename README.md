# AttendancePro v2.0 📸

::: {align="center"}
![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge&logo=appveyor)
![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/status-stable-success?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
:::

**AttendancePro** is a desktop application that uses computer vision to
automate attendance.\
It scans faces via a webcam, verifies them against a registered
database, and logs entries --- completely hands-free.

Originally built as **v1.0** during my 12th grade (Commerce + CS),
**v2.0** is a complete rewrite featuring a modern dark-mode UI, visual
analytics, and a modular architecture.

------------------------------------------------------------------------

## 📸 Interface Preview

### 📊 Dashboard

The central hub for analytics and quick statistics.

![Dashboard](screenshots/dashboard.png)

------------------------------------------------------------------------

### 👥 Student Management

  -------------------------------------------------------------------------------------------
                  Class Management                               Add New Student
  ------------------------------------------------- -----------------------------------------
                       ![Class                                        ![Add
   Management](screenshots/Class%20Management.png)   Student](screenshots/add%20student.png)

  -------------------------------------------------------------------------------------------

------------------------------------------------------------------------

### 🤖 Face Recognition in Action

  ---------------------------------------------------------------------------------------------------
                Recording Face Data                                Taking Attendance
  ------------------------------------------------ --------------------------------------------------
                    ![Recording                                         ![Taking
   Data](screenshots/recording%20face%20data.png)   Attendance](screenshots/taking%20attendance.png)

  ---------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 👨‍💻 The Story Behind This

> *"My goal is to become an AI/ML Engineer.\
> My strength is Computer Science and understanding the logic behind the
> magic."*

I started my academic journey in the **Commerce stream**, but my
curiosity for logic and algorithms pulled me into computer science.

------------------------------------------------------------------------

## 🧩 The Logic Behind the Magic

``` mermaid
graph TD
    Start((Launch App)) --> Dash[🏠 Dashboard]
    Dash --> Nav{User Action}
    Nav -- Add Student --> Form[📝 Enter Details]
    Form --> Cam1[📸 Capture Face]
    Store --> Save[(💾 Save to DB)]
    Nav -- Take Attendance --> Cam2[📹 Webcam]
    Cam2 --> Detect{Face Detected?}
    Detect -- Yes --> Log[✅ Mark Attendance]
```

------------------------------------------------------------------------

## 🚀 What's New in v2.0

-   Modern UI with CustomTkinter\
-   Visual analytics using Matplotlib\
-   SQLite database (no setup required)\
-   Modular and clean codebase

------------------------------------------------------------------------

## ⚡ How to Run

``` bash
git clone https://github.com/abhishekwadhwani2007/AttendancePro.git
cd AttendancePro
pip install -r requirements.txt
python main.py
```

------------------------------------------------------------------------

::: {align="center"}
Made with ❤️ by **Abhishek Wadhwani**
:::
