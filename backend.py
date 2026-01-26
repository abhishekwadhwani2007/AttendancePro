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
    
    try:
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        face_data = []
        skip = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)
            
            if len(faces) == 0:
                cv2.putText(frame, "No face detected", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Capturing Face - Press Q when done", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            x, y, w, h = faces[0] #Using [:1] to handle one face at a time
            #Padding
            offset = 5
            
            face_section = frame[max(y - offset, 0): y + h + offset,
                                max(x - offset, 0): x + w + offset]
            face_selection = cv2.resize(face_section, (100, 100))
            
            if skip % 5 == 0:
                face_data.append(face_selection)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Captured: {len(face_data)}/{samples}", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Capturing Face - Press Q when done", frame)
            
            skip += 1
            
            if cv2.waitKey(1) & 0xFF == ord('q') and len(face_data) > 20:
                break
        
        face_data = np.array(face_data).reshape((len(face_data), -1)) # flatten makes this [[1],[2]] to [1, 2]
        np.save(os.path.join(DATASET_DIR, name), face_data)
        
        cap.release()
        cv2.destroyAllWindows()
        
        speak("Face data saved successfully")
        return True
        
    except Exception as e:
        print(f"Error recording face: {str(e)}")
        return False

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
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return None
            
        face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
        
        matched_name = None
        last_marked = None
        status_message = ""
        message_timer = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 6)
            
            matched_name = None
            
            for (x, y, w, h) in faces:
                #Padding
                offset = 5
                face_section = frame[max(y-offset, 0): y+h+offset,
                                    max(x-offset, 0): x+w+offset]
                
                if face_section.size == 0:
                    continue
                
                face_section = cv2.resize(face_section, (100, 100))
                out = knn(trainset, face_section.flatten()) #knn function will compare the detected face's features with the training data (trainset) and return the predicted label and flatten makes this [[1],[2]] to [1, 2] 
                candidate_name = names[int(out)]
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, candidate_name, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                matched_name = candidate_name
            
            cv2.putText(frame, "Press 'N' to mark | 'Q' to quit", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.putText(frame, f"Marked: {len(marked_students)}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            if last_marked:
                cv2.putText(frame, f"Last: {last_marked}", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if status_message and message_timer > 0:
                cv2.putText(frame, status_message, (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                message_timer -= 1
            
            cv2.imshow("Face Recognition", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('n') and matched_name:
                student = db_module.get_student_by_name(matched_name)
                
                if student:
                    student_id = student[0]
                    
                    if not db_module.check_attendance_exists(student_id, current_date):
                        db_module.mark_attendance(student_id, current_date, current_time, "P")
                        speak(f"{matched_name} marked present")
                        marked_students.append(matched_name)
                        last_marked = matched_name
                        status_message = f"SUCCESS: {matched_name} marked!"
                        message_timer = 90
                        print(f"✓ {matched_name} marked present at {current_time}")
                    else:
                        speak(f"{matched_name} already marked")
                        status_message = f"ALREADY MARKED: {matched_name}"
                        message_timer = 90
                        print(f"! {matched_name} already marked today")
                else:
                    status_message = f"ERROR: {matched_name} not in database"
                    message_timer = 90
                    print(f"✗ Student {matched_name} not found in database")
            
            if key == ord('q'):
                break
        
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