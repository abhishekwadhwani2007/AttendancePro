import numpy as np
import cv2
import os
import urllib.request
import sys
import json
import datetime
import pyttsx3
import re

# Base paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATASET_DIR = os.path.join(BASE_DIR, "face_dataset")
HAARCASCADE_PATH = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")

def check_and_download_haarcascade(target_path):
    if not os.path.exists(target_path):
        print(f"⚠️ Haarcascade file missing. Downloading to: {target_path}")
        url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        
        try:
            urllib.request.urlretrieve(url, target_path)
            print("✅ Download complete.")
        except Exception as e:
            print(f"❌ Error downloading file: {str(e)}")
            print("Please download 'haarcascade_frontalface_default.xml' manually and place it in the project folder.")
            return False
    return True

os.makedirs(DATASET_DIR, exist_ok=True)

def load_config():
    check_and_download_haarcascade(HAARCASCADE_PATH)
    default = {
        "dataset_dir": DATASET_DIR,
        "camera_index": 0,
        "recognition_threshold": 0.6,
        "samples_per_student": 50,
    }
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                default.update(config)
        except Exception:
            pass
    return default


def face_data_filename(name):
    safe_name = re.sub(r"[^A-Za-z0-9_. -]+", "_", name.strip()).strip("._ ")
    return safe_name or "student"


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def get_camera_index():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return int(json.load(f).get("camera_index", 0))
    except Exception:
        pass
    return 0


try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', 1)
    tts_enabled = True
except Exception:
    tts_enabled = False


def speak(text):
    if tts_enabled:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass


def distance(v1, v2):
    return np.sqrt(((v1 - v2) ** 2).sum())


def knn(train, test, k=5):
    dist = []
    
    for i in range(train.shape[0]):
        ix = train[i, :-1]
        iy = train[i, -1]
        d = distance(test, ix)
        dist.append([d, iy])
    
    dk = sorted(dist, key=lambda x: x[0])[:k]
    labels = np.array(dk)[:, -1]
    output = np.unique(labels, return_counts=True)
    index = np.argmax(output[1])
    return output[0][index]


def load_face_data():
    face_data = []
    labels = []
    class_id = 0
    names = {}
    
    try:
        npy_files = [f for f in os.listdir(DATASET_DIR) if f.endswith(".npy")]
    except Exception as e:
        return None, None
    
    if not npy_files:
        return None, None
    
    for fx in npy_files:
        names[class_id] = fx[:-4]
        data_item = np.load(os.path.join(DATASET_DIR, fx))
        face_data.append(data_item)
        target = class_id * np.ones((data_item.shape[0]))
        class_id += 1
        labels.append(target)
    
    face_dataset = np.concatenate(face_data, axis=0)
    face_labels = np.concatenate(labels, axis=0).reshape((-1, 1))
    trainset = np.concatenate((face_dataset, face_labels), axis=1)
    
    return names, trainset


def _draw_rounded_rect(img, pt1, pt2, color, thickness, r=12):
    """Draw a rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r),  90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r),   0, 0, 90, color, thickness)


def _apply_dark_titlebar(window_name):
    """Turn the Windows title bar dark using the DWM API."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        if hwnd:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass


def record_face(name, samples=50):
    speak(f"Recording face for {name}")

    # OpenCV uses BGR color order.
    PURPLE    = (246, 92, 139)   # #8B5CF6
    DARK_CARD = (19, 17, 17)     # #111113
    WHITE     = (252, 250, 248)  # #F8FAFC
    MUTED     = (184, 163, 148)  # #94A3B8
    GREEN     = (129, 185, 16)   # #10B981
    RED       = (68, 68, 239)    # #EF4444

    cap = None
    window_name = f"AttendancePro - Capture: {name}"
    try:
        cap = cv2.VideoCapture(get_camera_index())
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return False

        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        face_data = []
        skip = 0
        saved = False
        first_frame = True

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            h_frame, w_frame = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)

            face_detected = False
            if len(faces) > 0:
                faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                x, y, w, h = faces[0]
                offset = 5
                face_section = frame[max(y - offset, 0): y + h + offset,
                                     max(x - offset, 0): x + w + offset]
                if face_section.size > 0:
                    face_detected = True
                    face_selection = cv2.resize(face_section, (100, 100))
                    if skip % 3 == 0 and len(face_data) < samples:
                        face_data.append(face_selection)
                    _draw_rounded_rect(frame, (x, y), (x + w, y + h), PURPLE, 2)
                    cv2.putText(frame, name, (x, max(y - 12, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, PURPLE, 2)

            skip += 1

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0),             (w_frame, 85),       DARK_CARD, -1)
            cv2.rectangle(overlay, (0, h_frame - 70),  (w_frame, h_frame),  DARK_CARD, -1)
            cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

            cv2.rectangle(frame, (0, 0), (w_frame, 3), PURPLE, -1)

            cv2.putText(frame, f"Capturing: {name}", (15, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, WHITE, 2)

            # Progress bar
            progress_pct = min(1.0, len(face_data) / max(1, samples))
            bar_x, bar_y, bar_w, bar_h = 15, 50, w_frame - 30, 14
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 45, 45), -1)
            fill_w = int(bar_w * progress_pct)
            if fill_w > 0:
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), PURPLE, -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (90, 80, 80), 1)
            pct_text = f"{int(progress_pct * 100)}%  ({len(face_data)}/{samples})"
            cv2.putText(frame, pct_text, (bar_x + bar_w + 8, bar_y + 11),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, MUTED, 1)

            if len(face_data) >= samples:
                cv2.putText(frame, "Target reached!  Saving...", (15, h_frame - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, GREEN, 2)
                cv2.imshow(window_name, frame)
                cv2.waitKey(600)
                saved = True
                break
            elif not face_detected:
                cv2.putText(frame, "Please position your face in front of the camera", (15, h_frame - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.58, RED, 1)

            cv2.putText(frame, "S - Save early     Q - Cancel", (15, h_frame - 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, WHITE, 2)

            cv2.imshow(window_name, frame)
            if first_frame:
                _apply_dark_titlebar(window_name)
                first_frame = False
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') and len(face_data) > 0:
                saved = True; break
            elif key == ord('q'):
                saved = False; break
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    saved = len(face_data) > 0
                    break
            except Exception:
                pass

        if saved and len(face_data) > 0:
            face_array = np.array(face_data).reshape((len(face_data), -1))
            np.save(os.path.join(DATASET_DIR, face_data_filename(name)), face_array)
            speak("Face data saved successfully")
            return True
        else:
            speak("No face samples captured" if len(face_data) == 0 else "Face capture cancelled")
            return False

    except Exception as e:
        print(f"Error recording face: {str(e)}")
        return False
    finally:
        if cap is not None: cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)


def recognize_and_mark_attendance(db_module):
    loaded = load_face_data()
    if loaded == (None, None):
        return None

    names, trainset = loaded
    current_date = str(datetime.date.today())
    marked_students = []
    speak("Starting face recognition")

    # OpenCV uses BGR color order.
    PURPLE    = (246, 92, 139)
    DARK_CARD = (19, 17, 17)
    WHITE     = (252, 250, 248)
    MUTED     = (184, 163, 148)
    GREEN     = (129, 185, 16)
    ORANGE    = (0, 165, 255)
    RED       = (68, 68, 239)

    cap = None
    window_name = "AttendancePro - Face Recognition"
    try:
        cap = cv2.VideoCapture(get_camera_index())
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return None

        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        matched_name  = None
        last_marked   = None
        status_msg    = ""
        status_color  = GREEN
        msg_timer     = 0
        first_frame   = True

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            h_frame, w_frame = frame.shape[:2]
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)
            matched_name = None

            for (x, y, w, h) in faces:
                offset = 5
                face_section = frame[max(y - offset, 0): y + h + offset,
                                     max(x - offset, 0): x + w + offset]
                if face_section.size == 0:
                    continue
                face_section  = cv2.resize(face_section, (100, 100))
                out           = knn(trainset, face_section.flatten())
                candidate     = names.get(int(out), "Unknown")
                matched_name  = candidate
                _draw_rounded_rect(frame, (x, y), (x + w, y + h), PURPLE, 2)
                cv2.putText(frame, candidate, (x, max(y - 12, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, PURPLE, 2)

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0),            (w_frame, 85),      DARK_CARD, -1)
            cv2.rectangle(overlay, (0, h_frame - 55), (w_frame, h_frame), DARK_CARD, -1)
            cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

            cv2.rectangle(frame, (0, 0), (w_frame, 3), PURPLE, -1)

            marked_text = f"Marked today: {len(marked_students)}"
            cv2.putText(frame, "AttendancePro | Face Recognition", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
            cv2.putText(frame, marked_text, (w_frame - 220, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, PURPLE, 2)

            detected_str = f"Detected: {matched_name}" if matched_name else "Scanning for face..."
            detected_col = PURPLE if matched_name else MUTED
            cv2.putText(frame, detected_str, (15, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, detected_col, 2)

            if last_marked:
                cv2.putText(frame, f"Last marked: {last_marked}", (w_frame - 280, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, GREEN, 1)

            if status_msg and msg_timer > 0:
                cv2.putText(frame, status_msg, (15, h_frame - 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                msg_timer -= 1

            cv2.putText(frame, "M - Mark Present     Q - Quit", (15, h_frame - 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, WHITE, 2)

            cv2.imshow(window_name, frame)
            if first_frame:
                _apply_dark_titlebar(window_name)
                first_frame = False
            key = cv2.waitKey(1) & 0xFF

            if key == ord('m') and matched_name:
                student = db_module.get_student_by_name(matched_name)
                if student:
                    sid = student[0]
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    if not db_module.check_attendance_exists(sid, current_date):
                        db_module.mark_attendance(sid, current_date, current_time, "P")
                        speak(f"{matched_name} marked present")
                        marked_students.append(matched_name)
                        last_marked  = matched_name
                        status_msg   = f"Marked present: {matched_name}"
                        status_color = GREEN
                        msg_timer    = 90
                    else:
                        speak(f"{matched_name} already marked")
                        status_msg   = f"Already marked: {matched_name}"
                        status_color = ORANGE
                        msg_timer    = 90
                else:
                    status_msg   = f"Not in database: {matched_name}"
                    status_color = RED
                    msg_timer    = 90

            if key == ord('q'):
                break
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                pass

        return marked_students

    except Exception as e:
        print(f"Error during recognition: {str(e)}")
        return None
    finally:
        if cap is not None: cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

def delete_face_data(name):
    face_file = os.path.join(DATASET_DIR, f"{face_data_filename(name)}.npy")
    if os.path.exists(face_file):
        os.remove(face_file)


def validate_phone_number(phone):
    if not phone.startswith("+"):
        phone = "+91" + phone
    return phone


def calculate_attendance_percentage(student_id, db_module, days=30):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    
    reports = db_module.get_attendance_reports(
        str(start_date), 
        str(end_date), 
        None
    )
    
    student_attendance = [r for r in reports if r[1] == student_id]
    present_days = len([a for a in student_attendance if a[6] == "P"])
    
    if days == 0:
        return 0
    
    return (present_days / days) * 100


def export_to_csv(data, headers, filename):
    import csv
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in data:
                writer.writerow(row)
        return True
    except Exception as e:
        print(f"Export error: {str(e)}")
        return False
