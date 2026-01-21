import cv2
import numpy as np 
import pyttsx3
import datetime
import requests
import mysql.connector as cm
import os
import tkinter as tk
from dotenv import load_dotenv
from tkinter import messagebox, ttk,Tk, Text, filedialog, END
import csv

#TextToSpeech Setup
engine = pyttsx3.init()
    # Set properties
engine.setProperty('rate', 150) # Speed of speech
engine.setProperty('volume', 1) # Volume (0.0 to 1.0)

entry = False
current_date = datetime.datetime.now().date()
load_dotenv()

#MySQL Setup
conn = cm.connect(host='localhost',password = os.getenv('DB_PASSWORD'), user='root', database ='attendance')
cur = conn.cursor()
cur.execute("SELECT * FROM master")
mdata = cur.fetchall()
cur.execute("SELECT * FROM january")
adata = cur.fetchall()


#Welcoming The User
engine.say("welcome")
engine.runAndWait()

def record_data():
    #Reloading the recods
    cur.execute("SELECT * FROM master")
    mdata = cur.fetchall()
    cur.execute("SELECT * FROM january")
    adata = cur.fetchall()

    fill_details_window() 

def recognise_face():
    #Reloading the recods
    cur.execute("SELECT * FROM master")
    mdata = cur.fetchall()
    cur.execute("SELECT * FROM january")
    adata = cur.fetchall()
    
    current_date = datetime.datetime.now().date()
    engine.say("Recognising")
    engine.runAndWait()

    #Distance
    def distance(v1, v2): #v1 = test (test sample feature) v2 = ix (current training sample feature).
        return np.sqrt(((v1 - v2) ** 2).sum()) #npsqrt makes ([1,4,9,16]) ([1,2,3,4])
    
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
    
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    dataset_path = "./face_dataset/"

    face_data = []
    labels = []  # Labels for every given file
    class_id = 0
    names = {}  # For mapping between id and name

    for fx in os.listdir(dataset_path):  # Getting each file or folder name in directory.
        if fx.endswith(".npy"):
            names[class_id] = fx[:-4]  # Removing .npy for Getting Name
            data_item = np.load(dataset_path + fx)  # Loads data from a file in dataset_path
            face_data.append(data_item)
            target = class_id * np.ones((data_item.shape[0])) # The target variable is used to give every photo of a person their ID.
            class_id += 1
            labels.append(target)
    face_dataset = np.concatenate(face_data, axis=0)# stacks all the face data vertically into one big array from this [[1.1, 2.2, 3.3]] to [1.1, 2.2, 3.3]
    face_labels = np.concatenate(labels, axis=0).reshape((-1, 1))  # Get a single, one-dimensional array with all labels and to give same id to same face
    trainset = np.concatenate((face_dataset, face_labels), axis=1)  #As to give dataset a label

    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.3, 6)
        for face in faces: 
            x, y, w, h = face
            #Padding
            offset = 5
            face_section = frame[y - offset:y + h + offset, x - offset:x + w + offset]
            face_section = cv2.resize(face_section, (100, 100))

            out = knn(trainset, face_section.flatten()) #knn function will compare the detected face's features with the training data (trainset) and return the predicted label and flatten makes this [[1],[2]] to [1, 2] 

            cv2.putText(frame, names[int(out)], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
            matched_name = names[int(out)]

        cv2.imshow("Recognising", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            def record_entry():
                if not adata:  # If adata is empty
                    return True
                else:
                    for i in adata:
                        if matched_name == i[2] and i[5] == current_date:
                            return False
                    return True

            record_list = []
            for record in mdata:
                if record[2] == matched_name:
                    record_list = record
                    break

            if record_entry():
                cur.execute(
                    "INSERT INTO january VALUES({}, {}, '{}', {}, '{}', '{}', '{}')".format(
                        record_list[0], record_list[1], record_list[2],
                        record_list[3], record_list[4], current_date, "P"))
                conn.commit()


                if record_list[5] == "M":
                    engine.say(matched_name + " Present")
                    engine.runAndWait()
                    try:
                        apisecret = os.getenv("SMS_API_SECRET")
                        deviceid = os.getenv('SMS_DEVICE_ID')
                        phone_no = record_list[6]   
                        msg = matched_name + " is marked present today"

                        connection = {"secret": apisecret, "mode" : "devices", "device" : deviceid, "sim" : 1, "priority" : 1, "phone" : phone_no, "message" : msg}
                        r = requests.get(url = "https://www.cloud.smschef.com/api/send/sms", params = connection)
                        result = r.json()
                        messagebox.showinfo("Message Info", "Message is sent")

                    except Exception as e:
                        messagebox.showerror("Error sending SMS:", "Error: No phone number is associated with the student details, or An error occurred while sending the SMS.")
                        print(e)
                else:
                    engine.setProperty('voice', engine.getProperty('voices')[1].id)
                    engine.say(matched_name + " Present")
                    engine.runAndWait()
            else:
                for j in adata:
                    if record_list[0] == j[0] and j[5] == current_date:
                        if record_list[5] == "M":
                            engine.say("Already Present")
                            engine.runAndWait()
                        else:
                            engine.setProperty('voice', engine.getProperty('voices')[1].id)
                            engine.say("Already Present")
                            engine.runAndWait()
                        break
            break
    cap.release()  
    cv2.destroyAllWindows()  
    start_button_clicked()

def view_attendance():
    engine.say("View Attendance")
    engine.runAndWait()
    view_attendance_window = tk.Toplevel(root)
    view_attendance_window.title("View Attendance")
    view_attendance_window.attributes('-fullscreen', True)

    sky_blue = '#87CEEB'
    view_attendance_window.configure(bg=sky_blue)

    def on_back_to_options():
        view_attendance_window.destroy()  
        start_button_clicked()  

    heading_label = tk.Label(view_attendance_window, text="View Attendance", font=("Times New Roman", 40), bg=sky_blue)
    heading_label.pack(pady=40)

    input_frame = tk.Frame(view_attendance_window, bg=sky_blue)
    input_frame.pack(pady=30)

    details = [("Name", "name"), ("Std", "std"), ("Section", "section")]
    entry_vars = {}  # To store entry variables

    for i, (label_text, var_name) in enumerate(details):   #To keep track with index number
        # Label for each field
        label = tk.Label(input_frame, text=f"{label_text}:", font=("Times New Roman", 20), bg=sky_blue, anchor='w')
        label.grid(row=i, column=0, padx=20, pady=20, sticky='w')  # Padding added here

        # Entry field for each field
        entry_var = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=entry_var, font=("Times New Roman", 20))
        entry.grid(row=i, column=1, padx=20, pady=20)  # Padding added here

        entry_vars[var_name] = entry_var

    button_frame = tk.Frame(view_attendance_window, bg=sky_blue)
    button_frame.pack(pady=50)

    back_button = tk.Button(button_frame, text="Back", command=on_back_to_options,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    back_button.pack(side="left", padx=50)

    def on_next():
        data = {k: v.get() for k, v in entry_vars.items()}  # Retrieve data from fields
            
        # Check if "name", "std", and "section" are empty or not
        if not data["name"] and not data["std"] and not data["section"]:
            messagebox.showwarning("Input Error", "Please provide atleast one value to proceed ")

        else:
            # Query the database based on the provided data
            name = data["name"]
            std = data["std"]
            section = data["section"]


            if not data["section"] and not data["std"]:
                cur.execute("SELECT * FROM january WHERE {} = '{}'".format("name", name))
            
            elif not data["section"] and not data['std']:
                cur.execute("SELECT * FROM january WHERE {} = '{}'".format("name", name))

            elif not data["name"] and not data['std']: 
                cur.execute("SELECT * FROM january WHERE {} = '{}'".format("section", section))

            elif not data["name"] and not data['section']: 
                cur.execute("SELECT * FROM january WHERE {} = {}".format("std", std))

            elif not data['name']:
                cur.execute("SELECT * FROM january WHERE {} = '{}' AND {} = {}".format("section", section, "std", std))

            elif not data['std']:
                cur.execute("SELECT * FROM january WHERE {} = '{}' AND {} = '{}'".format("section", section, "name", name))

            elif not data['section']:
                cur.execute("SELECT * FROM january WHERE {} = '{}' AND {} = {}".format("name", name, "std", std))

            else:
                messagebox.showinfo("No Record Found", "No matching record found in the database.")

            attendance_data = cur.fetchall()
            
            if attendance_data:
                view_attendance_window.destroy()
                display_record_window(attendance_data)
            else:
                messagebox.showinfo("No Record Found", "No matching record found in the database.")

    next_button = tk.Button(button_frame, text="Next", command=on_next,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    next_button.pack(side="right", padx=50)
    
    
def display_record_window(attendance_data):
    display_window = tk.Toplevel(root)
    display_window.title("Attendance Record")
    engine.say("Attendance Record")
    engine.runAndWait()
    display_window.attributes('-fullscreen', True)

    sky_blue = '#87CEEB'
    display_window.configure(bg=sky_blue)

    heading_label = tk.Label(display_window, text="Attendance Record", font=("Times New Roman", 40), bg=sky_blue)
    heading_label.pack(pady=40)

    table_frame = tk.Frame(display_window, bg=sky_blue)
    table_frame.pack(fill="both", expand=True, padx=50, pady=20)

    columns = ("Grno", "Rollno", "Name", "Std", "Section", "Date", "Attendance")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    for row in attendance_data:
        tree.insert("", "end", values=row)
    tree.pack(fill="both", expand=True)

    button_frame = tk.Frame(display_window, bg=sky_blue)
    button_frame.pack(pady=50)

    def on_back_to_view_attendance():
        display_window.destroy()
        view_attendance()

    def on_exit():
        display_window.destroy()

    def on_download():
        engine.say("Downloading")
        engine.runAndWait()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("Text file", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:  # Check if the user provided a file name
            try:
                with open(file_path, mode='w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(columns)  # column headers
                    writer.writerows(attendance_data)  # data rows
                
                messagebox.showinfo("Download Successful", f"Attendance data saved as:\n{file_path}")
        
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
    
        else:
            messagebox.showinfo("Cancelled", "File saving was cancelled.")

    back_button = tk.Button(button_frame, text="Back", command=on_back_to_view_attendance,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    back_button.pack(side="left", padx=50)

    exit_button = tk.Button(button_frame, text="Exit", command=on_exit,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    exit_button.pack(side="right", padx=25)

    download_button = tk.Button(button_frame, text="Download", command=on_download,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    download_button.pack(side="left", padx=50)

def fill_details_window():
    data_window = tk.Toplevel(root)
    data_window.title("Fill the Details")
    data_window.attributes('-fullscreen', True)
    engine.say("Fill the Details")
    engine.runAndWait()    
    sky_blue = '#87CEEB'
    data_window.configure(bg=sky_blue)
    
    def on_close_data_window():
        data_window.destroy()
        start_button_clicked() 

    heading_label = tk.Label(data_window, text="Fill the Details", font=("Times New Roman", 40), bg=sky_blue)
    heading_label.pack(pady=40)

    input_frame = tk.Frame(data_window, bg=sky_blue)
    input_frame.pack(pady=20)

    details = [("Grno", "grno"), ("Roll No", "rollno"), ("Name", "name"), 
               ("Std", "std"), ("Section", "section"), ("Gender", "gender"), ('Phoneno', "phoneno")]    
    
    entry_vars = {} # Dictionary to store entry variables

    for detail, var_name in details:
        label = tk.Label(input_frame, text=detail + ":", font=("Times New Roman", 20), bg=sky_blue, anchor='w')
        label.grid(row=details.index((detail, var_name)), column=0, padx=10, pady=10, sticky='w')
        
        entry_var = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=entry_var, font=("Times New Roman", 20))
        entry.grid(row=details.index((detail, var_name)), column=1, padx=10, pady=10)
        
        entry_vars[var_name] = entry_var  
    button_frame = tk.Frame(data_window, bg=sky_blue)
    button_frame.pack(pady=50)

    back_button = tk.Button(button_frame, text="Back", command=on_close_data_window,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    back_button.pack(side="left", padx=50)


    def on_next_data():
        data = {k: v.get() for k, v in entry_vars.items()}
    
        if all(data.values()):  # Check if none of the fields are empty
            grno = int(data['grno'])
            rollno = int(data['rollno'])
            name = data['name']
            std = int(data['std'])
            section = data['section'].title()
            gender = data['gender'].upper()
            phoneno = data['phoneno']
            if phoneno[0]=='+' and phoneno[1] == "9" and phoneno[2] == '1':
                phoneno = phoneno
            else:
                phoneno = "+91"+phoneno

            def record_face(grno, rollno, name, std, section, gender):
                engine.say("Starting recording")
                engine.runAndWait()
                cap = cv2.VideoCapture(0)
                face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

                skip = 0
                face_data = []
                dataset_path = "./face_dataset/"

                while True:
                    ret, frame = cap.read()
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    if not ret:
                        continue

                    faces = face_cascade.detectMultiScale(gray_frame, 1.3, 6)
                    if len(faces) == 0:
                        continue
                    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)

                    for face in faces[:1]: #Using [:1] to handle one face at a time
                        x, y, w, h = face
                        #Giving Padding
                        offset = 5
                        face_offset = frame[y-offset:y+h+offset, x-offset:x+w+offset]
                        face_selection = cv2.resize(face_offset, (100, 100))

                        if skip % 5 == 0:
                            face_data.append(face_selection)

                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.imshow("Capturing Face", frame)

                    key_pressed = cv2.waitKey(1) & 0xFF
                    if key_pressed == ord('q'):
                            break

                if len(face_data) >= 0:
                    face_data = np.array(face_data)
                    face_data = face_data.reshape((face_data.shape[0], -1))
                
                    if mdata == []:
                        cur.execute("INSERT INTO master VALUES ({},{},'{}',{},'{}','{}', '{}')".format(grno, rollno, name, std, section, gender, phoneno))
                        conn.commit()
                        np.save(dataset_path + name, face_data)
                        if gender == "M":
                            print("Data Saved")
                            engine.say("Data Saved")
                            engine.runAndWait()
                            
                        else:
                            engine.setProperty('voice', engine.getProperty('voices')[1].id)
                            print("Data Saved")
                            engine.say("Data Saved")
                            engine.runAndWait()
                    else:

                        for i in mdata:
                            if grno != i[0] or mdata == []:
                                cur.execute("INSERT INTO master VALUES ({},{},'{}',{},'{}','{}', '{}')".format(grno, rollno, name, std, section, gender, phoneno))
                                conn.commit()
                                np.save(dataset_path + name, face_data)
                                if gender == "M":
                                    print("Data Saved")
                                    engine.say("Data Saved")
                                    engine.runAndWait()
                                    break
                                else:
                                    engine.setProperty('voice', engine.getProperty('voices')[1].id)
                                    print("Data Saved")
                                    engine.say("Data Saved")
                                    engine.runAndWait()
                                    break
                            elif grno == i[0]:
                                if gender == "M":
                                    print("Already in Database")
                                    engine.say("Already in Database")
                                    engine.runAndWait()
                                    break
                                else:
                                    engine.setProperty('voice', engine.getProperty('voices')[1].id)
                                    print("Already in Database")
                                    engine.say("Already in Database")
                                    engine.runAndWait()
                                    break
                    cap.release()
                    cv2.destroyAllWindows()   
            record_face(grno, rollno, name, std, section, gender)
            data_window.destroy()  
            start_button_clicked()

        else:
            Warning.config(text="Please fill in all fields!") 
    
    next_button = tk.Button(button_frame, text="Next", command=on_next_data,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    next_button.pack(side="right", padx=50)

def start_button_clicked():
    root.withdraw()
    engine.runAndWait()
    options_window = tk.Toplevel(root)
    options_window.title("Options")
    options_window.attributes('-fullscreen', True)
    engine.say("Choose the Option")
    engine.runAndWait()
    sky_blue = '#87CEEB'
    options_window.configure(bg=sky_blue)
    
    def on_close():
        root.deiconify()
        root.state('zoomed')
        options_window.destroy()
    
    options_window.protocol("WM_DELETE_WINDOW", on_close)
    
    heading_label = tk.Label(options_window, text="Choose the Function to Perform",
                             font=("Times New Roman", 40), bg=sky_blue)
    heading_label.pack(pady=80)
    
    checkbox_frame = tk.Frame(options_window, bg=sky_blue)
    checkbox_frame.pack(pady=40)
    
    add_data_var = tk.IntVar()
    give_attendance_var = tk.IntVar()
    view_attendance_var = tk.IntVar()

    # Uncheck other checkboxes if one is selected
    def on_add_data_selected():
        if add_data_var.get() == 1:
            give_attendance_var.set(0)
            view_attendance_var.set(0)

    def on_give_attendance_selected():
        if give_attendance_var.get() == 1:
            add_data_var.set(0)
            view_attendance_var.set(0)
    
    def on_view_attendance_selected():
        if view_attendance_var.get() == 1:
            add_data_var.set(0)
            give_attendance_var.set(0)

    # Add checkboxes
    add_data_check = tk.Checkbutton(checkbox_frame, text="Add Data", variable=add_data_var,
                                    font=("Times New Roman", 30), bg=sky_blue,
                                    selectcolor="#d8bfd8", command=on_add_data_selected, anchor='w')
    add_data_check.pack(anchor='w', padx=50, pady=20)

    give_attendance_check = tk.Checkbutton(checkbox_frame, text="Give Attendance", variable=give_attendance_var,
                                           font=("Times New Roman", 30), bg=sky_blue,
                                           selectcolor="#d8bfd8", command=on_give_attendance_selected, anchor='w')
    give_attendance_check.pack(anchor='w', padx=50, pady=20)

    view_attendance_check = tk.Checkbutton(checkbox_frame, text="View Attendance", variable=view_attendance_var,
                                           font=("Times New Roman", 30), bg=sky_blue,
                                           selectcolor="#d8bfd8", command=on_view_attendance_selected, anchor='w')
    view_attendance_check.pack(anchor='w', padx=50, pady=20)

    button_frame = tk.Frame(options_window, bg=sky_blue)
    button_frame.pack(pady=50)

    back_button = tk.Button(button_frame, text="Back", command=on_close,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    back_button.pack(side="left", padx=50)

    def on_next_clicked():
        if add_data_var.get() == 1:
            record_data()  # Open "Fill the Details" window if "Add Data" is selected
            options_window.destroy()
        elif give_attendance_var.get() == 1:
            recognise_face()
            options_window.destroy()
        elif view_attendance_var.get() == 1:
            view_attendance()  # Open "View Attendance" window
            options_window.destroy()

    next_button = tk.Button(button_frame, text="Next", command=on_next_clicked,
                            font=("Times New Roman", 24), bg='lightgrey', relief="raised", bd=5)
    next_button.pack(side="right", padx=30)

root = tk.Tk()
root.title("Face Attendance")
root.state('zoomed')

bg_color = '#e6f2ff'  # Light royal blue background
root.configure(bg=bg_color)

welcome_label = tk.Label(root, text="Welcome to Face Attendance", font=("Times New Roman", 40),
                         bg=bg_color, fg='#003366')
welcome_label.pack(expand=True, fill="both", pady=20)

button_frame = tk.Frame(root, bg=bg_color)
button_frame.pack(fill="x", pady=20)    

start_button = tk.Button(button_frame, text="Start", command=start_button_clicked,
                         font=("Times New Roman", 20), bg='lightgrey', relief="raised", bd=5)
start_button.pack(fill="x", padx=50)

root.mainloop()