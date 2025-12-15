"""
BayanWatch Database Configuration
Python database connection using SQLite
"""

import sqlite3
import os
import bcrypt
import threading

class DatabaseConnection:
    """
    Manages database connections for BayanWatch system
    """

    def __init__(self):
        """Initialize database configuration"""
        self.database = 'bayanwatch.db'
        self.local = threading.local()

    def _get_connection(self):
        """Get thread-local connection"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.database)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection

    def _get_cursor(self):
        """Get thread-local cursor"""
        if not hasattr(self.local, 'cursor'):
            self.local.cursor = self._get_connection().cursor()
        return self.local.cursor

    def connect(self):
        """
        Establish connection to SQLite database
        Returns: connection object or None
        """
        try:
            connection = self._get_connection()
            print(f"✅ Successfully connected to SQLite database: {self.database}")
            return connection

        except sqlite3.Error as e:
            print(f"❌ Error connecting to SQLite: {e}")
            return None

    def disconnect(self):
        """Close database connection"""
        if hasattr(self.local, 'connection'):
            self.local.connection.close()
            print("🔌 SQLite connection closed")

    def execute_query(self, query, params=None):
        """
        Execute a query (INSERT, UPDATE, DELETE)
        Args:
            query: SQL query string
            params: tuple of parameters for prepared statement
        Returns: affected rows count or last inserted id for INSERT
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(query, params or ())
            self._get_connection().commit()

            # For INSERT queries, return the last inserted row id
            if query.strip().upper().startswith('INSERT'):
                last_id = cursor.lastrowid
                print(f"✅ INSERT executed successfully. Last inserted ID: {last_id}")
                return last_id
            else:
                affected_rows = cursor.rowcount
                print(f"✅ Query executed successfully. {affected_rows} row(s) affected.")
                return affected_rows

        except sqlite3.Error as e:
            print(f"❌ Error executing query: {e}")
            if hasattr(self.local, 'connection'):
                self.local.connection.rollback()
            return 0

    def fetch_query(self, query, params=None):
        """
        Execute a SELECT query and fetch results
        Args:
            query: SQL query string
            params: tuple of parameters for prepared statement
        Returns: list of dictionaries (rows)
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()

            print(f"✅ Query executed successfully. {len(results)} row(s) fetched.")
            return [dict(row) for row in results]

        except sqlite3.Error as e:
            print(f"❌ Error fetching data: {e}")
            return []

    def fetch_one(self, query, params=None):
        """
        Execute a SELECT query and fetch one result
        Args:
            query: SQL query string
            params: tuple of parameters for prepared statement
        Returns: dictionary (single row) or None
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchone()

            if result:
                print(f"✅ Query executed successfully. 1 row fetched.")
                return dict(result)
            return None

        except sqlite3.Error as e:
            print(f"❌ Error fetching data: {e}")
            return None


# Global database instance
db = DatabaseConnection()


# Helper functions for common operations
def get_all_users():
    """Get all users from database"""
    query = "SELECT * FROM users ORDER BY created_at DESC"
    return db.fetch_query(query)


def get_user_by_id(user_id):
    """Get user by ID"""
    query = "SELECT * FROM users WHERE id = ?"
    return db.fetch_one(query, (user_id,))


def get_all_complaints(access_code=None):
    """Get all complaints, optionally filtered by access_code"""
    # Map access codes to barangay names
    access_code_to_barangay = {
        "ADMIN123": "Barangay Malitam, Batangas City",
        "BARANGAY456": "Barangay Libjo, Batangas City",
        "OFFICIAL789": "Barangay Sorosoro Karsada, Batangas City"
    }

    if access_code:
        barangay_name = access_code_to_barangay.get(access_code, "")
        query = """
            SELECT c.*, u.full_name as author_full_name, ? as barangay_location
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE u.access_code = ?
            ORDER BY c.created_at DESC
        """
        return db.fetch_query(query, (barangay_name, access_code))
    else:
        # Get all complaints with barangay based on access code
        query = """
            SELECT c.*, u.full_name as author_full_name,
                   CASE u.access_code
                       WHEN 'ADMIN123' THEN 'Barangay Malitam, Batangas City'
                       WHEN 'BARANGAY456' THEN 'Barangay Libjo, Batangas City'
                       WHEN 'OFFICIAL789' THEN 'Barangay Sorosoro Karsada, Batangas City'
                       ELSE ''
                   END as barangay_location
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
        """
        return db.fetch_query(query)


def get_complaints_by_status(status):
    """Get complaints filtered by status"""
    query = """
        SELECT c.*, u.full_name as author_full_name
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE c.status = ?
        ORDER BY c.created_at DESC
    """
    return db.fetch_query(query, (status,))


def get_user_complaints(user_id):
    """Get all complaints by a specific user"""
    query = """
        SELECT * FROM complaints
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    return db.fetch_query(query, (user_id,))


def create_user(full_name, password, role='resident', access_code=None, **kwargs):
    """Create a new user"""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    query = """
        INSERT INTO users (full_name, password_hash, role, access_code)
        VALUES (?, ?, ?, ?)
    """
    user_id = db.execute_query(query, (full_name, hashed_password, role, access_code))

    # If user is an official, add barangay information
    if role == 'official' and user_id:
        barangay_location = kwargs.get('barangay_location')
        barangay_hotline = kwargs.get('barangay_hotline')
        barangay_captain = kwargs.get('barangay_captain')
        barangay_residents = kwargs.get('barangay_residents')

        if barangay_location and barangay_hotline and barangay_captain and barangay_residents is not None:
            barangay_query = """
                INSERT INTO barangay_info (user_id, barangay_location, barangay_hotline, barangay_captain, barangay_residents)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_query(barangay_query, (user_id, barangay_location, barangay_hotline, barangay_captain, barangay_residents))

    return user_id


def update_complaint_status(complaint_id, new_status):
    """Update complaint status"""
    query = "UPDATE complaints SET status = ? WHERE id = ?"
    return db.execute_query(query, (new_status, complaint_id))


def delete_complaint(complaint_id):
    """Delete a complaint"""
    query = "DELETE FROM complaints WHERE id = ?"
    return db.execute_query(query, (complaint_id,))


def verify_password(full_name, password, access_code=None):
    """Verify user password and optionally access code"""
    if access_code:
        query = "SELECT id, full_name, password_hash, role, access_code FROM users WHERE full_name = ? AND access_code = ?"
        user = db.fetch_one(query, (full_name, access_code))
    else:
        query = "SELECT id, full_name, password_hash, role, access_code FROM users WHERE full_name = ?"
        user = db.fetch_one(query, (full_name,))

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return user
    return None


def create_complaint(user_id, description, category='Others', location=None, media_path=None):
    """Create a new complaint"""
    query = """
        INSERT INTO complaints (user_id, description, category, location, media_path)
        VALUES (?, ?, ?, ?, ?)
    """
    complaint_id = db.execute_query(query, (user_id, description, category, location, media_path))
    return complaint_id


def get_statistics():
    """Get system statistics"""
    stats = {}

    # Total users
    query = "SELECT COUNT(*) as count FROM users"
    result = db.fetch_one(query)
    stats['total_users'] = result['count'] if result else 0

    # Total complaints
    query = "SELECT COUNT(*) as count FROM complaints"
    result = db.fetch_one(query)
    stats['total_complaints'] = result['count'] if result else 0

    # Complaints by status
    query = """
        SELECT status, COUNT(*) as count
        FROM complaints
        GROUP BY status
    """
    status_counts = db.fetch_query(query)
    stats['by_status'] = {row['status']: row['count'] for row in status_counts}

    # Total comments
    query = "SELECT COUNT(*) as count FROM comments"
    result = db.fetch_one(query)
    stats['total_comments'] = result['count'] if result else 0

    # Total likes
    query = "SELECT COUNT(*) as count FROM likes"
    result = db.fetch_one(query)
    stats['total_likes'] = result['count'] if result else 0

    return stats


# Comments functions
def get_comments_for_complaint(complaint_id):
    """Get all comments for a specific complaint"""
    query = """
        SELECT c.*, u.full_name as author_name
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.complaint_id = ?
        ORDER BY c.created_at ASC
    """
    return db.fetch_query(query, (complaint_id,))


def add_comment(complaint_id, user_id, comment_text):
    """Add a new comment to a complaint"""
    query = """
        INSERT INTO comments (complaint_id, user_id, comment_text)
        VALUES (?, ?, ?)
    """
    return db.execute_query(query, (complaint_id, user_id, comment_text))


def delete_comment(comment_id, user_id):
    """Delete a comment (only by the author)"""
    query = "DELETE FROM comments WHERE id = ? AND user_id = ?"
    return db.execute_query(query, (comment_id, user_id))


# Likes functions
def get_likes_count(complaint_id):
    """Get the number of likes for a complaint"""
    query = "SELECT COUNT(*) as count FROM likes WHERE complaint_id = ?"
    result = db.fetch_one(query, (complaint_id,))
    return result['count'] if result else 0


def has_user_liked(complaint_id, user_id):
    """Check if a user has liked a complaint"""
    query = "SELECT id FROM likes WHERE complaint_id = ? AND user_id = ?"
    result = db.fetch_one(query, (complaint_id, user_id))
    return result is not None


def toggle_like(complaint_id, user_id):
    """Toggle like for a complaint (add if not liked, remove if liked)"""
    if has_user_liked(complaint_id, user_id):
        # Remove like
        query = "DELETE FROM likes WHERE complaint_id = ? AND user_id = ?"
        result = db.execute_query(query, (complaint_id, user_id))
        return False  # Return False to indicate like was removed
    else:
        # Add like
        query = "INSERT INTO likes (complaint_id, user_id) VALUES (?, ?)"
        result = db.execute_query(query, (complaint_id, user_id))
        return True  # Return True to indicate like was added


# Barangay backgrounds functions
def get_barangay_background(access_code):
    """Get background image for a specific access code/barangay"""
    query = "SELECT background_path FROM barangay_backgrounds WHERE access_code = ?"
    result = db.fetch_one(query, (access_code,))
    return result['background_path'] if result and result['background_path'] else None


def set_barangay_background(access_code, background_path, uploaded_by=None):
    """Set background image for a specific access code/barangay"""
    query = """
        INSERT OR REPLACE INTO barangay_backgrounds (access_code, background_path, uploaded_by, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """
    return db.execute_query(query, (access_code, background_path, uploaded_by))


def get_all_barangay_backgrounds():
    """Get all barangay backgrounds"""
    query = "SELECT access_code, background_path FROM barangay_backgrounds ORDER BY access_code"
    return db.fetch_query(query)


# Example usage
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 BayanWatch Python Database Connection Test")
    print("="*60 + "\n")
    
    # Connect to database
    db.connect()
    
    if db.connection:
        print("\n📊 Fetching system statistics...\n")
        stats = get_statistics()
        
        print(f"👥 Total Users: {stats['total_users']}")
        print(f"📝 Total Complaints: {stats['total_complaints']}")
        print(f"💬 Total Comments: {stats['total_comments']}")
        print(f"\n📋 Complaints by Status:")
        for status, count in stats.get('by_status', {}).items():
            print(f"   - {status}: {count}")
        
        print("\n" + "="*60)
        
        # Disconnect
        db.disconnect()
    
    print("\n✨ Test completed!\n")