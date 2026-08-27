import numpy as np
import cv2
import os
import urllib.request
import sys
import json
import datetime
import pyttsx3

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


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150) # Speed of speech
    tts_engine.setProperty('volume', 1) # Volume (0.0 to 1.0)
    tts_enabled = True
except:
    tts_enabled = False


def speak(text):
    if tts_enabled:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except:
            pass


def distance(v1, v2): #v1 = test (test sample feature) v2 = ix (current training sample feature).
    return np.sqrt(((v1 - v2) ** 2).sum()) #npsqrt makes ([1,4,9,16]) to ([1,2,3,4])


def knn(train, test, k=5):
    dist = []
    
    for i in range(train.shape[0]):
        #train is a 2D NumPy array where each row represents a training sample where last column is label
        ix = train[i, :-1] #ix is used to store the feature vector (all features except the label) 
        iy = train[i, -1] #iy is a variable used to store the label (class) of the current training sample.
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
        names[class_id] = fx[:-4] # Removing .npy for Getting Name
        data_item = np.load(os.path.join(DATASET_DIR, fx))
        face_data.append(data_item)
        target = class_id * np.ones((data_item.shape[0])) # The target variable is used to give every photo of a person their ID.
        class_id += 1
        labels.append(target)
    
    face_dataset = np.concatenate(face_data, axis=0)# stacks all the face data vertically into one big array from this [[1.1, 2.2, 3.3]] to [1.1, 2.2, 3.3]
    face_labels = np.concatenate(labels, axis=0).reshape((-1, 1)) # Get a single, one-dimensional array with all labels and to give same id to same face
    trainset = np.concatenate((face_dataset, face_labels), axis=1) #As to give dataset a label
    
    return names, trainset


def record_face(name, samples=50):
    speak(f"Recording face for {name}")
    
    cap = None
    window_name = f"Capturing Face - {name}"
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return False
            
        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        face_data = []
        skip = 0
        saved = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            h_frame, w_frame = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)
            
            if len(faces) > 0:
                faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                x, y, w, h = faces[0]  # Using [:1] to handle one face at a time
                offset = 5
                
                face_section = frame[max(y - offset, 0): y + h + offset,
                                    max(x - offset, 0): x + w + offset]
                if face_section.size > 0:
                    face_selection = cv2.resize(face_section, (100, 100))
                    
                    if skip % 3 == 0 and len(face_data) < samples:
                        face_data.append(face_selection)
                    
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x, max(y - 10, 20)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No face detected - Look at camera", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            skip += 1
            
            # --- Top Header Overlay ---
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w_frame, 80), (20, 20, 20), -1)
            cv2.rectangle(overlay, (0, h_frame - 60), (w_frame, h_frame), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
            
            # Header text
            cv2.putText(frame, f"Student: {name}", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Progress text and bar
            progress_pct = min(1.0, len(face_data) / max(1, samples))
            cv2.putText(frame, f"Samples: {len(face_data)}/{samples}", (15, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            bar_x = 220
            bar_y = 48
            bar_w = 200
            bar_h = 18
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress_pct), bar_y + bar_h), (0, 255, 0), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 1)

            # Footer / Controls text
            if len(face_data) >= samples:
                cv2.putText(frame, "Target reached! Saving automatically...", (15, h_frame - 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow(window_name, frame)
                cv2.waitKey(400)
                saved = True
                break
            else:
                cv2.putText(frame, "Press 'S' to Save early | 'Q' to Cancel", (15, h_frame - 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s') and len(face_data) > 0:  # S = save with whatever we have so far
                saved = True
                break
            elif key == ord('q'):  # Q = cancel, don't save
                saved = False
                break
                
            # Window close button 'X' clicked
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    if len(face_data) > 0:
                        saved = True
                    break
            except Exception:
                pass
        
        if saved and len(face_data) > 0:
            face_array = np.array(face_data).reshape((len(face_data), -1))
            np.save(os.path.join(DATASET_DIR, name), face_array)
            speak("Face data saved successfully")
            return True
        else:
            if len(face_data) == 0:
                speak("No face samples captured")
            else:
                speak("Face capture cancelled")
            return False
            
    except Exception as e:
        print(f"Error recording face: {str(e)}")
        return False
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

def recognize_and_mark_attendance(db_module):
    loaded = load_face_data()
    if loaded == (None, None):
        return None
    
    names, trainset = loaded
    current_date = str(datetime.date.today())
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    marked_students = []
    
    speak("Starting face recognition")
    
    cap = None
    window_name = "AttendancePro - Face Recognition"
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return None
            
        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        
        matched_name = None
        last_marked = None
        status_message = ""
        status_color = (0, 255, 0)
        message_timer = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            h_frame, w_frame = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)
            
            matched_name = None
            
            for (x, y, w, h) in faces:
                offset = 5
                face_section = frame[max(y-offset, 0): y+h+offset,
                                    max(x-offset, 0): x+w+offset]
                
                if face_section.size == 0:
                    continue
                
                face_section = cv2.resize(face_section, (100, 100))
                out = knn(trainset, face_section.flatten())
                candidate_name = names.get(int(out), "Unknown")
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, candidate_name, (x, max(y - 10, 20)),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                matched_name = candidate_name
            
            # --- Top & Bottom Overlays ---
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w_frame, 80), (20, 20, 20), -1)
            cv2.rectangle(overlay, (0, h_frame - 60), (w_frame, h_frame), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
            
            # Top stats
            cv2.putText(frame, f"Attendance Mode | Marked: {len(marked_students)}", (15, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            
            detected_str = f"Detected: {matched_name}" if matched_name else "Scanning for face..."
            detected_col = (0, 255, 0) if matched_name else (200, 200, 200)
            cv2.putText(frame, detected_str, (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, detected_col, 2)
            
            if last_marked:
                cv2.putText(frame, f"Last: {last_marked}", (w_frame - 260, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            
            # Message banner
            if status_message and message_timer > 0:
                cv2.putText(frame, status_message, (15, h_frame - 75),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
                message_timer -= 1
            
            # Bottom control instructions
            cv2.putText(frame, "Press 'M' to Mark Present | 'Q' to Exit", (15, h_frame - 22),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # M = mark attendance
            if key == ord('m') and matched_name:
                student = db_module.get_student_by_name(matched_name)
                
                if student:
                    student_id = student[0]
                    
                    if not db_module.check_attendance_exists(student_id, current_date):
                        current_time = datetime.datetime.now().strftime("%H:%M:%S")
                        db_module.mark_attendance(student_id, current_date, current_time, "P")
                        speak(f"{matched_name} marked present")
                        marked_students.append(matched_name)
                        last_marked = matched_name
                        status_message = f"SUCCESS: {matched_name} marked present!"
                        status_color = (0, 255, 0)
                        message_timer = 90
                        print(f"✓ {matched_name} marked present at {current_time}")
                    else:
                        speak(f"{matched_name} already marked")
                        status_message = f"ALREADY MARKED: {matched_name}"
                        status_color = (0, 165, 255)
                        message_timer = 90
                        print(f"! {matched_name} already marked today")
                else:
                    status_message = f"ERROR: {matched_name} not found in database"
                    status_color = (0, 0, 255)
                    message_timer = 90
                    print(f"✗ Student {matched_name} not found in database")
            
            # Q = quit
            if key == ord('q'):
                break
                
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                pass
        
        print(f"\nTotal marked: {len(marked_students)}")
        if marked_students:
            for name in marked_students:
                print(f"  ✓ {name}")
        
        return marked_students
        
    except Exception as e:
        print(f"Error during recognition: {str(e)}")
        return None
        
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

def delete_face_data(name):
    face_file = os.path.join(DATASET_DIR, f"{name}.npy")
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
            writer.writerow(headers) # column headers
            for row in data:
                writer.writerow(row) # data rows
        return True
    except Exception as e:
        print(f"Export error: {str(e)}")
        return False