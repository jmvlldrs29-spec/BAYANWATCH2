import sqlite3

def setup_database():
    """Set up the BayanWatch database and tables using SQLite"""
    try:
        # Connect to SQLite database
        connection = sqlite3.connect('bayanwatch.db')
        cursor = connection.cursor()
        print("✅ Connected to SQLite database")

        # Read and execute schema.sql
        with open('schema.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # Split the script into individual statements
        statements = sql_script.split(';')

        for statement in statements:
            statement = statement.strip()
            if statement:  # Skip empty statements
                cursor.execute(statement)
                print(f"✅ Executed: {statement[:50]}...")

        connection.commit()
        print("✅ Database and tables created successfully!")

        cursor.close()
        connection.close()
        print("🔌 SQLite connection closed")

    except sqlite3.Error as e:
        print(f"❌ Error setting up database: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 BayanWatch Database Setup")
    print("="*60 + "\n")
    setup_database()
    print("\n✨ Setup completed!\n")
