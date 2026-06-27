import mysql.connector
import bcrypt
from datetime import datetime

class DBManager:
    def __init__(self):
        self.config = {
            'user': 'root',
            'password': '',
            'host': '127.0.0.1',
            'database': 'lpr_system', 
            'raise_on_warnings': True
        }

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def process_detection(self, id, plate_text, vehicle_type, image_path, camera_name, ocrs, method):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            gate_number = 1 if 'camera1' in camera_name else 2

            check_query = "SELECT * FROM registration_table WHERE plate_number = %s"
            cursor.execute(check_query, (plate_text,))
            result = cursor.fetchone()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if result:
                status_string = "Registered"
            else:
                status_string = "No Gate Pass"
                if plate_text.strip()=='':
                    status_string = "Unidentifiable"

            insert_query = """
            INSERT INTO transaction_table 
                (transaction_id, plate_number, status, date_time, vehicle_type, gate_number, saved_picture, guard_on_duty, ocrs, method) 
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, (SELECT `employee_id` FROM `user_table` WHERE `active` = 1 LIMIT 1), %s, %s) 
            ON DUPLICATE KEY UPDATE 
                plate_number  = VALUES(plate_number),
                status        = VALUES(status),
                date_time     = VALUES(date_time),
                vehicle_type  = VALUES(vehicle_type),
                gate_number   = VALUES(gate_number),
                saved_picture = VALUES(saved_picture),
                guard_on_duty = VALUES(guard_on_duty),
                ocrs          = VALUES(ocrs),
                method        = VALUES(method);
            """
            
            vals = (id, plate_text, status_string, current_time, vehicle_type, gate_number, image_path, ",".join(ocrs), method)
            cursor.execute(insert_query, vals)
            conn.commit()
            
            # print(f"Logged {plate_text} as {status_string}")

            plate = plate_text
            query = f"SELECT * FROM `watchlist_table` WHERE watchlist_table.plate_number='{plate}'"
            cursor.execute(query)
            result = cursor.fetchone()
            detected_watchlist = None
            if result:
                detected_watchlist = [plate,current_time,gate_number]

            return status_string, detected_watchlist

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return "Error"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def register_new_user(self, userid, username, password):
        # print("registering")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "INSERT INTO user_table (employee_id, name, password, last_login) VALUES (%s, %s, %s, %s)"
            # print(query)
            cursor.execute(query, (userid, username, hashed_password, datetime.today().strftime('%Y-%m-%d')))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"SQL Error during registration: {err}")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def verify_user(self, userid, pwd):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 1. Fetch the user's hash, active status, and role using ONLY the employee_id.
            # Note: Using %s instead of f-strings prevents SQL injection attacks.
            query = "SELECT password, active, role FROM user_table WHERE employee_id = %s"
            cursor.execute(query, (userid,))
            user_record = cursor.fetchone()

            # 2. Check if the user actually exists in the database
            if user_record:
                # 3. Verify the password using bcrypt
                provided_pwd_bytes = pwd.encode('utf-8')
                stored_hash_bytes = user_record['password'].encode('utf-8')

                # checkpw() handles the salt and the slow hashing comparison
                if bcrypt.checkpw(provided_pwd_bytes, stored_hash_bytes):
                    
                    # 4. Check if account is already active
                    if user_record['active'] == 1:
                        return False, "Someone is currently logged in to this account!"
                    
                    # 5. Update the login timestamp and set active to 1
                    update_query = "UPDATE user_table SET last_login = NOW(), active = 1 WHERE employee_id = %s"
                    cursor.execute(update_query, (userid,))
                    conn.commit()
                    
                    # 6. Return True and the role we fetched in step 1
                    return True, {"role": user_record['role']}
                
                else:
                    # Password didn't match
                    return False, "Invalid Employee ID or Password"
            else:
                # Employee ID wasn't found
                return False, "Invalid Employee ID or Password"

        except mysql.connector.Error as err:
            print(f"Login Database Error: {err}")
            return False, "Database error occurred"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    # def database_query(self, query):
    #     conn = None
    #     try:
    #         conn = self.get_connection()
    #         cursor = conn.cursor(dictionary=True)
    #         cursor.execute(query)
    #         result = cursor.fetchall()
            
    #         if result:
    #             return True, result
    #         else:
    #             return False, "Unknown error occured."
    #     except mysql.connector.Error as err:
    #         print(f"Login Database Error: {err}")
    #         return False, "Database error occurred"
    #     finally:
    #         if conn and conn.is_connected():
    #             cursor.close()
    #             conn.close()
    
    def database_query(self, query):
        conn = None
        cursor = None # Initialize cursor as None just to be safe
        try:
            conn = self.get_connection()
            # Added buffered=True here as an extra safety net
            cursor = conn.cursor(dictionary=True, buffered=True) 
            cursor.execute(query)
            
            # THE FIX: Check if the cursor has a description (meaning it has results to fetch)
            if cursor.description is not None:
                result = cursor.fetchall()
                if result:
                    return True, result
                else:
                    return False, "No results found."
            else:
                # For DELETE, INSERT, UPDATE: We must COMMIT
                conn.commit()
                
                # Check if any rows were actually affected
                if cursor.rowcount > 0:
                    return True, f"Success. Rows affected: {cursor.rowcount}"
                else:
                    return False, "No rows were affected."
                
        except mysql.connector.Error as err:
            print(f"Login Database Error: {err}")
            print(f"Error Caused By: {query}")
            return False, str(err)
        finally:
            # Added a check to ensure cursor exists before trying to close it
            if cursor is not None:
                cursor.close()
            if conn is not None and conn.is_connected():
                conn.close()


db = DBManager()

if __name__ == "__main__":
    plates = []
    result = db.database_query("SELECT `plate_number`,IF(`first_name`= '', `last_name`, CONCAT(`last_name`, ', ' , `first_name`)) as 'full_name' FROM `unregistered_plates`")[1]
    for item in result:
        fullname = item['full_name']
        plate =item['plate_number']
        if fullname.strip()[0] == "#":
            continue
        plates.append((fullname,plate))
    print(plates)