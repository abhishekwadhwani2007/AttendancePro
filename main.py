import db_logic 
import backend 
import frontend 

if __name__ == "__main__":

    db_logic.init_db()
    config = backend.load_config()
    app = frontend.AttendanceProApp(db_logic, backend, config)
    app.mainloop()