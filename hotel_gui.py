import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import sqlite3
import random

# --- RE-INTEGRATE BACKEND CLASSES HERE ---
# Assuming the user provided all the classes (DatabaseManager, HotelSystem)
# and global variables (CURRENT_USER_ROLE, CURRENT_USERNAME)
# are defined in the same script for a single-file solution.

# --- Global State for Current User Role and Username ---
CURRENT_USER_ROLE = None
CURRENT_USERNAME = None # Stores the unique username of the logged-in user

# ----------------------------------------------------
# DatabaseManager Class (As provided by the user)
# ----------------------------------------------------
class DatabaseManager:
    """
    Manages all database interactions for the hotel management system.
    """

    def __init__(self, db_name='hotel.db'):
        """Initializes the database connection and creates tables if they do not exist."""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._seed_initial_data()

    def _create_tables(self):
        # 1. Create rooms table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_number INTEGER PRIMARY KEY,
                room_type TEXT NOT NULL,
                price REAL NOT NULL,
                is_available BOOLEAN DEFAULT TRUE
            )
        ''')

        # 2. Create guests table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                id_number TEXT
            )
        ''')

        # Safely add the missing 'id_number' column if needed 
        try:
            self.cursor.execute("ALTER TABLE guests ADD COLUMN id_number TEXT")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                pass
            
        # 3. Create bookings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER NOT NULL,
                room_number INTEGER NOT NULL,
                check_in_date TEXT NOT NULL,
                check_out_date TEXT NOT NULL,
                FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
                FOREIGN KEY (room_number) REFERENCES rooms(room_number)
            )
        ''')
        
        # 4. Create users table (Staff)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # 5. Create TASKS table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number INTEGER NOT NULL,
                assigned_user_id INTEGER,
                task_type TEXT NOT NULL, -- e.g., 'Cleanup', 'Maintenance'
                status TEXT DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Completed'
                FOREIGN KEY (room_number) REFERENCES rooms(room_number),
                FOREIGN KEY (assigned_user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()

    def _seed_initial_data(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('admin', 'adminpass', 'Admin')
            )
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('user', 'userpass', 'User')
            )
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('housekeeper1', 'housepass', 'User')
            )
            self.conn.commit()
            # In GUI, we skip the print statement
    
    def authenticate_user(self, username, password):
        self.cursor.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    # --- TASK ASSIGNMENT METHODS ---

    def get_available_housekeepers(self):
        self.cursor.execute("SELECT user_id FROM users WHERE role = 'User'")
        return [row[0] for row in self.cursor.fetchall()]

    def assign_cleanup_task(self, room_number):
        available_housekeepers = self.get_available_housekeepers()
        if not available_housekeepers:
            return None

        placeholders = ','.join('?' for _ in available_housekeepers)
        
        query = f"""
            SELECT
                u.user_id,
                COUNT(t.task_id) AS active_tasks
            FROM users u
            LEFT JOIN tasks t ON u.user_id = t.assigned_user_id
                AND t.status IN ('Pending', 'In Progress')
            WHERE u.user_id IN ({placeholders})
            GROUP BY u.user_id
            ORDER BY active_tasks ASC, RANDOM()
            LIMIT 1
        """
        self.cursor.execute(query, available_housekeepers)
        result = self.cursor.fetchone()

        if result:
            assigned_user_id = result[0]
            
            self.cursor.execute(
                "SELECT task_id FROM tasks WHERE room_number = ? AND status IN ('Pending', 'In Progress')", 
                (room_number,)
            )
            if self.cursor.fetchone():
                return 'Already Assigned' 
                
            self.cursor.execute(
                "INSERT INTO tasks (room_number, assigned_user_id, task_type) VALUES (?, ?, ?)",
                (room_number, assigned_user_id, 'Cleanup')
            )
            self.conn.commit()
            
            self.cursor.execute("SELECT username FROM users WHERE user_id = ?", (assigned_user_id,))
            username = self.cursor.fetchone()[0]
            
            return username
        return None

    def get_tasks_by_staff(self, user_id):
        self.cursor.execute('''
            SELECT task_id, room_number, task_type, status 
            FROM tasks WHERE assigned_user_id = ? 
            ORDER BY status DESC, room_number
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_user_id_by_username(self, username):
        self.cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_task_status(self, task_id, new_status):
        if new_status == 'Completed':
             self.cursor.execute("SELECT room_number FROM tasks WHERE task_id = ?", (task_id,))
             room_number = self.cursor.fetchone()
             if room_number:
                  self.cursor.execute(
                      "UPDATE rooms SET is_available = TRUE WHERE room_number = ?",
                      (room_number[0],)
                  )

        self.cursor.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (new_status, task_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0
        
    def get_all_pending_tasks(self):
        self.cursor.execute('''
            SELECT t.task_id, t.room_number, t.task_type, t.status, u.username
            FROM tasks t
            LEFT JOIN users u ON t.assigned_user_id = u.user_id
            ORDER BY t.status, t.room_number
        ''')
        return self.cursor.fetchall()

    # --- END TASK ASSIGNMENT METHODS ---

    def add_user(self, username, password, role):
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False 

    def get_all_users(self):
        self.cursor.execute("SELECT user_id, username, role FROM users")
        return self.cursor.fetchall()

    def delete_user(self, user_id):
        try:
            self.cursor.execute("UPDATE tasks SET assigned_user_id = NULL WHERE assigned_user_id = ?", (user_id,))
            self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0 
        except Exception:
            return False
            
    def add_room(self, room_number, room_type, price):
        try:
            self.cursor.execute(
                "INSERT INTO rooms (room_number, room_type, price) VALUES (?, ?, ?)",
                (room_number, room_type, price)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Return False instead of printing error to handle in GUI

    def get_all_rooms(self):
        self.cursor.execute("SELECT * FROM rooms")
        return self.cursor.fetchall()
        
    def get_room_availability(self, room_number):
        self.cursor.execute("SELECT is_available FROM rooms WHERE room_number = ?", (room_number,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def add_guest(self, name, contact_number, id_number):
        self.cursor.execute(
            "INSERT INTO guests (name, contact_number, id_number) VALUES (?, ?, ?)",
            (name, contact_number, id_number)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_guest_id_by_name(self, name):
        self.cursor.execute("SELECT guest_id FROM guests WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def book_room(self, guest_id, room_number, check_in_date, check_out_date):
        self.cursor.execute(
            "INSERT INTO bookings (guest_id, room_number, check_in_date, check_out_date) VALUES (?, ?, ?, ?)",
            (guest_id, room_number, check_in_date, check_out_date)
        )
        self.cursor.execute(
            "UPDATE rooms SET is_available = FALSE WHERE room_number = ?",
            (room_number,)
        )
        self.conn.commit()
        return True

    def checkout_room(self, room_number):
        self.cursor.execute("SELECT is_available FROM rooms WHERE room_number = ?", (room_number,))
        is_available_status = self.cursor.fetchone()
        
        if is_available_status is None:
            return False 
        
        if is_available_status[0] == 1:
            return False 

        self.cursor.execute(
             "DELETE FROM bookings WHERE room_number = ?",
             (room_number,)
        )
        
        assigned_staff = self.assign_cleanup_task(room_number)
        
        self.conn.commit()
        return assigned_staff


    def get_current_bookings(self):
        self.cursor.execute('''
            SELECT
                b.booking_id,
                g.name,
                r.room_number,
                b.check_in_date,
                b.check_out_date
            FROM bookings b
            JOIN guests g ON b.guest_id = g.guest_id
            JOIN rooms r ON b.room_number = r.room_number
            WHERE r.is_available = FALSE
        ''')
        return self.cursor.fetchall()

    def get_guest_personal_data(self):
        self.cursor.execute("SELECT guest_id, name, contact_number, id_number FROM guests")
        return self.cursor.fetchall()

    def get_room_display_data(self):
        # The complex query for room status view
        self.cursor.execute('''
            SELECT
                r.room_number,
                r.room_type,
                r.price,
                r.is_available,
                t.status AS task_status
            FROM rooms r
            LEFT JOIN tasks t ON r.room_number = t.room_number 
                AND t.status IN ('Pending', 'In Progress')
            ORDER BY r.room_number
        ''')
        return self.cursor.fetchall()

# ----------------------------------------------------
# HotelSystem Class (As provided by the user)
# ----------------------------------------------------
class HotelSystem:
    """
    Handles the business logic of the hotel management system.
    """

    def __init__(self):
        self.db_manager = DatabaseManager()

    def _check_role(self, required_role):
        """Helper function to check user role."""
        global CURRENT_USER_ROLE
        if CURRENT_USER_ROLE is None:
            return False
        # Allow 'Admin' to perform 'User' actions
        if required_role == 'User' and CURRENT_USER_ROLE in ['User', 'Admin']:
            return True
        if required_role == 'Admin' and CURRENT_USER_ROLE == 'Admin':
            return True
        return False

    # --- Methods modified for GUI to return data/status instead of printing ---

    def view_rooms_data(self):
        if not self._check_role('User'): return "Access Denied"
        rooms = self.db_manager.get_room_display_data()
        
        display_data = []
        for room in rooms:
            room_number, room_type, price, is_available, task_status = room
            
            if task_status is not None:
                status = "Needs Cleanup"
            elif not is_available:
                status = "Occupied"
            else:
                status = "Available"
                 
            display_data.append((room_number, room_type, f"${price:.2f}", status))
        
        return display_data

    def book_room_logic(self, guest_name, contact_number, id_number, room_number, check_in_date, check_out_date):
        if not self._check_role('User'): return "Access Denied: Log in required."
        try:
            room_number = int(room_number)
            is_available = self.db_manager.get_room_availability(room_number)
            
            if is_available is None:
                return f"Error: Room {room_number} does not exist."
            
            # Check for pending cleanup
            self.db_manager.cursor.execute("SELECT status FROM tasks WHERE room_number = ? AND status IN ('Pending', 'In Progress')", (room_number,))
            needs_cleanup = self.db_manager.cursor.fetchone()
            
            if not is_available or needs_cleanup:
                status_text = 'Needs Cleanup' if needs_cleanup else 'Occupied'
                return f"Error: Room {room_number} is not available (Status: {status_text})."

            guest_id = self.db_manager.get_guest_id_by_name(guest_name)
            if not guest_id:
                guest_id = self.db_manager.add_guest(guest_name, contact_number, id_number)
                guest_msg = f"New guest '{guest_name}' added."
            else:
                guest_msg = f"Existing guest '{guest_name}' found."
            
            if self.db_manager.book_room(guest_id, room_number, check_in_date, check_out_date):
                return f"SUCCESS: Room {room_number} booked for {guest_name}. {guest_msg}"
            return "Error: Could not complete booking."

        except Exception as e:
            return f"An unexpected error occurred during booking: {e}"

    def checkout_logic(self, room_number):
        if not self._check_role('User'): return "Access Denied: Log in required."
        try:
            room_number = int(room_number)
            assigned_staff = self.db_manager.checkout_room(room_number)
            
            if assigned_staff == False:
                 is_available = self.db_manager.get_room_availability(room_number)
                 if is_available is None:
                      return f"Error: Room {room_number} does not exist."
                 elif is_available:
                      return f"Error: Room {room_number} is already vacant."
                 
            elif assigned_staff == 'Already Assigned':
                 return f"SUCCESS: Guest checked out from room {room_number}. Cleanup task was already pending."
            elif assigned_staff:
                 return f"SUCCESS: Guest checked out from room {room_number}. Cleanup task assigned to **{assigned_staff}**."
            elif assigned_staff is None:
                 return f"SUCCESS: Guest checked out from room {room_number}. No housekeeper available for task assignment."
            
            return "Unknown error during checkout."
                 
        except ValueError:
            return "Error: Room number must be an integer."
        except Exception as e:
             return f"An unexpected error occurred during checkout: {e}"


    def get_staff_tasks(self):
        if not self._check_role('User'): return "Access Denied"
        
        user_id = self.db_manager.get_user_id_by_username(CURRENT_USERNAME)
        if CURRENT_USER_ROLE == 'Admin':
            return self.db_manager.get_all_pending_tasks()
        
        return self.db_manager.get_tasks_by_staff(user_id)
    
    def complete_task(self, task_id):
        if not self._check_role('User'): return "Access Denied"
        user_id = self.db_manager.get_user_id_by_username(CURRENT_USERNAME)
        
        # Admin can complete any task, User can only complete their own
        if CURRENT_USER_ROLE == 'User':
            tasks = self.db_manager.get_tasks_by_staff(user_id)
            task_to_complete = next((t for t in tasks if t[0] == task_id), None)
            if not task_to_complete:
                 return "Error: Task not found or not assigned to you."
            if task_to_complete[3] == 'Completed':
                 return "Error: Task is already completed."

        if self.db_manager.update_task_status(task_id, 'Completed'):
            return "SUCCESS: Task marked as Completed. Room is now available."
        return "Error: Could not update task status."
    
    # ... other methods similarly modified to return results/status

# ----------------------------------------------------
# Tkinter GUI Application
# ----------------------------------------------------

class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🏨 Hotel Management System")
        self.geometry("800x600")
        
        self.hotel_system = HotelSystem()
        
        self.current_frame = None
        self.show_login_frame()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Cleanly close the database connection."""
        try:
             self.hotel_system.db_manager.conn.close()
        except:
             pass # Already closed or not initialized
        self.destroy()

    def switch_frame(self, new_frame_class):
        """Destroys current frame and creates a new one."""
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = new_frame_class(self, self.hotel_system)
        self.current_frame.pack(fill='both', expand=True)

    def show_login_frame(self):
        """Switches to the Login frame."""
        self.switch_frame(LoginFrame)

    def show_main_menu(self):
        """Switches to the Main Menu frame."""
        self.switch_frame(MainMenuFrame)


class LoginFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="Hotel Management System", font=("Arial", 20, "bold")).pack(pady=20)
        tk.Label(self, text="Login", font=("Arial", 16)).pack(pady=10)

        # Username
        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        # Password
        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        # Login Button
        tk.Button(self, text="Login", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        global CURRENT_USER_ROLE, CURRENT_USERNAME
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        role = self.hotel_system.db_manager.authenticate_user(username, password)
        
        if role:
            CURRENT_USER_ROLE = role
            CURRENT_USERNAME = username
            messagebox.showinfo("Success", f"Login successful! Role: {role}")
            self.master.show_main_menu()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


class MainMenuFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        # Header
        header_text = f"Welcome, {CURRENT_USERNAME} ({CURRENT_USER_ROLE})! 👋"
        tk.Label(self, text=header_text, font=("Arial", 18, "bold"), fg="blue").pack(pady=20)

        # Buttons (Dynamically shown based on role)
        
        # 1. Add Room (Admin Only)
        if CURRENT_USER_ROLE == 'Admin':
            tk.Button(self, text="1. Add New Room", command=self.show_add_room).pack(fill='x', padx=100, pady=5)
            
        # 2. View Rooms (All Staff)
        tk.Button(self, text="2. View All Rooms", command=self.show_view_rooms).pack(fill='x', padx=100, pady=5)
        
        # 3. Book Room (All Staff)
        tk.Button(self, text="3. Book a Room", command=self.show_book_room).pack(fill='x', padx=100, pady=5)
        
        # 4. Check out (All Staff)
        tk.Button(self, text="4. Check Out a Guest", command=self.show_checkout).pack(fill='x', padx=100, pady=5)

        # 5. View Bookings (All Staff)
        tk.Button(self, text="5. View Current Bookings", command=self.show_view_bookings).pack(fill='x', padx=100, pady=5)

        # 6. Manage Tasks (All Staff)
        tk.Button(self, text="6. Manage Cleanup Tasks", command=self.show_manage_tasks).pack(fill='x', padx=100, pady=5)
        
        # 7. Staff Management (Admin Only)
        if CURRENT_USER_ROLE == 'Admin':
            tk.Button(self, text="7. Staff Management", command=lambda: messagebox.showinfo("Feature", "Staff Management not implemented in this GUI, see console code for logic.")).pack(fill='x', padx=100, pady=5)

        # 8. View Guest Data (Admin Only)
        if CURRENT_USER_ROLE == 'Admin':
            tk.Button(self, text="8. View Guest Personal Data", command=lambda: messagebox.showinfo("Feature", "Guest Data View not implemented in this GUI, see console code for logic.")).pack(fill='x', padx=100, pady=5)


        # Separator
        tk.Label(self, text="---", fg="gray").pack(fill='x', padx=100, pady=10)

        # 9. Logout
        tk.Button(self, text="9. Logout", command=self.logout).pack(fill='x', padx=100, pady=5)

        # 10. Exit
        tk.Button(self, text="10. Exit", command=self.master.on_close).pack(fill='x', padx=100, pady=5)


    def logout(self):
        global CURRENT_USER_ROLE, CURRENT_USERNAME
        CURRENT_USER_ROLE = None
        CURRENT_USERNAME = None
        messagebox.showinfo("Logout", "You have been logged out.")
        self.master.show_login_frame()

    # --- Frame Switching Methods ---
    def show_add_room(self):
        self.master.switch_frame(AddRoomFrame)

    def show_view_rooms(self):
        self.master.switch_frame(ViewRoomsFrame)
        
    def show_book_room(self):
        self.master.switch_frame(BookRoomFrame)
        
    def show_checkout(self):
        self.master.switch_frame(CheckoutFrame)

    def show_view_bookings(self):
        self.master.switch_frame(ViewBookingsFrame)

    def show_manage_tasks(self):
        self.master.switch_frame(ManageTasksFrame)


# ----------------------------------------------------
# Module Frames (Simulating the functions)
# ----------------------------------------------------

class AddRoomFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="➕ Add New Room (Admin)", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self, text="Room Number:").pack()
        self.num_entry = tk.Entry(self)
        self.num_entry.pack(pady=2)

        tk.Label(self, text="Room Type:").pack()
        self.type_entry = tk.Entry(self)
        self.type_entry.pack(pady=2)

        tk.Label(self, text="Price per Night:").pack()
        self.price_entry = tk.Entry(self)
        self.price_entry.pack(pady=2)

        tk.Button(self, text="Add Room", command=self.add_room).pack(pady=15)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def add_room(self):
        room_number = self.num_entry.get()
        room_type = self.type_entry.get()
        price = self.price_entry.get()

        try:
            num = int(room_number)
            prc = float(price)
            if self.hotel_system.db_manager.add_room(num, room_type, prc):
                 messagebox.showinfo("Success", f"Room {num} ({room_type}) added successfully.")
            else:
                 messagebox.showerror("Error", f"Room number {num} already exists.")
        except ValueError:
            messagebox.showerror("Input Error", "Room number must be an integer and price must be a number.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

class ViewRoomsFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="🛏️ All Room Statuses", font=("Arial", 16, "bold")).pack(pady=10)

        self.listbox = tk.Listbox(self, width=80, height=20)
        self.listbox.pack(pady=10, padx=20)
        
        self.load_rooms()
        
        tk.Button(self, text="Refresh", command=self.load_rooms).pack(pady=5)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def load_rooms(self):
        self.listbox.delete(0, tk.END)
        rooms = self.hotel_system.view_rooms_data()
        
        if rooms == "Access Denied":
             self.listbox.insert(tk.END, "Access Denied. Please log in.")
             return

        if not rooms:
            self.listbox.insert(tk.END, "No rooms found.")
            return

        # Header
        self.listbox.insert(tk.END, f"{'Room #':<10} {'Type':<15} {'Price':<10} {'Status':<20}")
        self.listbox.insert(tk.END, "-" * 55)
        
        for room in rooms:
             room_number, room_type, price, status = room
             display_line = f"{room_number:<10} {room_type:<15} {price:<10} {status:<20}"
             self.listbox.insert(tk.END, display_line)
             # Highlight 'Needs Cleanup' or 'Occupied'
             if 'Cleanup' in status:
                  self.listbox.itemconfig(tk.END, {'fg': 'red'})
             elif 'Occupied' in status:
                  self.listbox.itemconfig(tk.END, {'fg': 'orange'})

class BookRoomFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="📅 Book a Room", font=("Arial", 16, "bold")).pack(pady=10)

        # Room Info
        tk.Label(self, text="--- Room Info ---").pack()
        tk.Label(self, text="Room Number:").pack()
        self.room_num_entry = tk.Entry(self)
        self.room_num_entry.pack(pady=2)

        # Guest Info
        tk.Label(self, text="--- Guest Info ---").pack(pady=5)
        tk.Label(self, text="Guest Name:").pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack(pady=2)
        
        tk.Label(self, text="Contact Number:").pack()
        self.contact_entry = tk.Entry(self)
        self.contact_entry.pack(pady=2)

        tk.Label(self, text="ID/Passport Number:").pack()
        self.id_entry = tk.Entry(self)
        self.id_entry.pack(pady=2)

        # Check-in/out (simplified to current date + 1 day for GUI)
        
        tk.Button(self, text="Book Now", command=self.book_room).pack(pady=15)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def book_room(self):
        name = self.name_entry.get()
        contact = self.contact_entry.get()
        id_num = self.id_entry.get()
        room_num = self.room_num_entry.get()

        if not all([name, contact, id_num, room_num]):
             messagebox.showerror("Error", "All fields must be filled.")
             return

        # Simple Date handling for the GUI
        check_in = datetime.now().strftime("%Y-%m-%d") 
        check_out = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        result_msg = self.hotel_system.book_room_logic(name, contact, id_num, room_num, check_in, check_out)
        
        if result_msg.startswith("SUCCESS"):
             messagebox.showinfo("Booking Success", result_msg)
        else:
             messagebox.showerror("Booking Failed", result_msg)

class CheckoutFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="🚪 Guest Check Out", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self, text="Enter Room Number to Check Out:").pack()
        self.room_num_entry = tk.Entry(self)
        self.room_num_entry.pack(pady=5)

        tk.Button(self, text="Check Out", command=self.checkout).pack(pady=15)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def checkout(self):
        room_num = self.room_num_entry.get()
        if not room_num:
            messagebox.showerror("Input Error", "Please enter a room number.")
            return

        result_msg = self.hotel_system.checkout_logic(room_num)
        
        if result_msg.startswith("SUCCESS"):
             messagebox.showinfo("Checkout Success", result_msg)
        else:
             messagebox.showerror("Checkout Failed", result_msg)

class ViewBookingsFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="📋 Current Bookings", font=("Arial", 16, "bold")).pack(pady=10)

        self.listbox = tk.Listbox(self, width=80, height=15)
        self.listbox.pack(pady=10, padx=20)
        
        self.load_bookings()
        
        tk.Button(self, text="Refresh", command=self.load_bookings).pack(pady=5)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def load_bookings(self):
        self.listbox.delete(0, tk.END)
        bookings = self.hotel_system.db_manager.get_current_bookings()
        
        if not self.hotel_system._check_role('User'):
             self.listbox.insert(tk.END, "Access Denied. Please log in.")
             return

        if not bookings:
            self.listbox.insert(tk.END, "No current bookings found.")
            return

        # Header
        self.listbox.insert(tk.END, f"{'ID':<6} {'Guest Name':<20} {'Room':<8} {'Check-in':<15} {'Check-out':<15}")
        self.listbox.insert(tk.END, "-" * 65)
        
        for booking in bookings:
             b_id, name, room, check_in, check_out = booking
             display_line = f"{b_id:<6} {name:<20} {room:<8} {check_in:<15} {check_out:<15}"
             self.listbox.insert(tk.END, display_line)

class ManageTasksFrame(tk.Frame):
    def __init__(self, master, hotel_system):
        super().__init__(master)
        self.master = master
        self.hotel_system = hotel_system
        
        tk.Label(self, text="🧹 Manage Cleanup Tasks", font=("Arial", 16, "bold")).pack(pady=10)

        self.listbox = tk.Listbox(self, width=90, height=15)
        self.listbox.pack(pady=10, padx=20)
        
        self.load_tasks()
        
        tk.Label(self, text="Task ID to Mark Completed:").pack(pady=5)
        self.task_id_entry = tk.Entry(self)
        self.task_id_entry.pack(pady=2)

        tk.Button(self, text="Complete Task", command=self.complete_task).pack(pady=10)
        tk.Button(self, text="Refresh Tasks", command=self.load_tasks).pack(pady=5)
        tk.Button(self, text="Back to Menu", command=self.master.show_main_menu).pack(pady=5)

    def load_tasks(self):
        self.listbox.delete(0, tk.END)
        tasks = self.hotel_system.get_staff_tasks()
        
        if tasks == "Access Denied":
             self.listbox.insert(tk.END, "Access Denied. Please log in.")
             return

        if not tasks:
            self.listbox.insert(tk.END, "No tasks currently assigned.")
            return

        # Header depends on role
        if CURRENT_USER_ROLE == 'Admin':
             header = f"{'ID':<6} {'Room':<6} {'Type':<15} {'Status':<15} {'Assigned To':<15}"
        else: # User/Housekeeper
             header = f"{'ID':<6} {'Room':<6} {'Type':<15} {'Status':<15}"

        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, "-" * (len(header) + 20))
        
        for task in tasks:
             if CURRENT_USER_ROLE == 'Admin':
                task_id, room_number, task_type, status, username = task
                display_line = f"{task_id:<6} {room_number:<6} {task_type:<15} {status:<15} {username if username else 'UNASSIGNED':<15}"
             else:
                 task_id, room_number, task_type, status = task
                 display_line = f"{task_id:<6} {room_number:<6} {task_type:<15} {status:<15}"
             
             self.listbox.insert(tk.END, display_line)
             if status == 'Pending' or status == 'In Progress':
                  self.listbox.itemconfig(tk.END, {'fg': 'red'})

    def complete_task(self):
        task_id_str = self.task_id_entry.get()
        if not task_id_str:
             messagebox.showerror("Input Error", "Please enter a Task ID.")
             return
        
        try:
             task_id = int(task_id_str)
        except ValueError:
             messagebox.showerror("Input Error", "Task ID must be a number.")
             return

        result_msg = self.hotel_system.complete_task(task_id)

        if result_msg.startswith("SUCCESS"):
             messagebox.showinfo("Task Completion", result_msg)
             self.load_tasks() # Refresh list
             self.task_id_entry.delete(0, tk.END)
        else:
             messagebox.showerror("Task Failed", result_msg)


if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()
