import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from db_config import verify_password, create_user, get_all_complaints, create_complaint, update_complaint_status, delete_complaint, get_comments_for_complaint, add_comment, delete_comment, get_likes_count, toggle_like, has_user_liked

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

# Enable CORS for all routes
CORS(app)

print("🚀 Starting BayanWatch Flask server...")
print("📁 Template folder:", app.template_folder)
print("📁 Static folder:", app.static_folder)

@app.route("/")
def index():
    # For now, redirect to login since we need authentication
    # In a production app, you'd check for valid session/token
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    # This is the main dashboard after login
    return render_template("index.html")

@app.route("/dashboard/admin123")
def dashboard_admin123():
    # Dashboard for ADMIN123 access code - use main dashboard for now
    return render_template("index.html")

@app.route("/dashboard/barangay456")
def dashboard_barangay456():
    # Dashboard for BARANGAY456 access code
    return render_template("dashboard_barangay456.html")

@app.route("/dashboard/official789")
def dashboard_official789():
    # Dashboard for OFFICIAL789 access code - use main dashboard for now
    return render_template("index.html")

@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    try:
        # Get user's access code from localStorage (passed via query param or header)
        # In a production app, this would come from session/token
        access_code = request.args.get('access_code')  # Frontend will send this
        fetch_all = request.args.get('fetch_all', 'false').lower() == 'true'  # New parameter for barangay filtering

        # If fetch_all is true, get all complaints for filtering, otherwise filter by access code
        if fetch_all:
            complaints = get_all_complaints()  # Get all complaints without access code filter
        else:
            complaints = get_all_complaints(access_code)

        # Format complaints for frontend
        formatted_complaints = []
        for c in complaints:
            # Determine media type and URL
            media_url = None
            media_type = None
            if c.get('media_path'):
                media_url = c['media_path']
                # Determine media type from file extension
                if c['media_path'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    media_type = 'image'
                elif c['media_path'].lower().endswith(('.mp4', '.webm', '.ogg')):
                    media_type = 'video'

            # Get actual likes count and comments for this complaint
            likes_count = get_likes_count(c['id'])
            raw_comments = get_comments_for_complaint(c['id'])

            # Format comments for frontend compatibility
            formatted_comments = []
            for comment in raw_comments:
                formatted_comments.append({
                    "id": comment["id"],
                    "author": comment["author_name"],
                    "text": comment["comment_text"],
                    "time_ago": "Just now"  # For now, use simple time ago
                })

            formatted_complaints.append({
                "id": c['id'],
                "author": c['author_full_name'],
                "initials": c['author_full_name'][:2].upper(),
                "text": c['description'],
                "category": c['category'],
                "location": c['location'] or "",
                "status": c['status'],
                "timeAgo": "Just now",  # For now, we'll use a simple time ago
                "mediaUrl": media_url,
                "mediaType": media_type,
                "likes": likes_count,
                "comments": formatted_comments,
                "barangay": c.get('barangay_location', '')  # Add barangay info for filtering
            })

        return jsonify(formatted_complaints)
    except Exception as e:
        print(f"Error fetching complaints: {e}")
        return jsonify([]), 500

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    full_name = data.get('full_name')
    password = data.get('password')
    role = data.get('role', 'resident')

    if not full_name or not password:
        return jsonify({"success": False, "message": "Full name and password are required"}), 400

    # Validate access code for all roles
    access_code = data.get('access_code')
    if not access_code:
        return jsonify({"success": False, "message": "Access code is required"}), 400

    # Validate access code - support multiple barangays
    valid_access_codes = {
        "ADMIN123": "Barangay Malitam, Batangas City",
        "BARANGAY456": "Barangay Libjo, Batangas City",
        "OFFICIAL789": "Barangay Sorosoro Karsada, Batangas City"
    }

    if access_code not in valid_access_codes:
        return jsonify({"success": False, "message": "Invalid access code"}), 400

    # Additional validation for officials
    if role == 'official':
        barangay_location = data.get('barangay_location')
        barangay_hotline = data.get('barangay_hotline')
        barangay_residents = data.get('barangay_residents')
        barangay_captain = data.get('barangay_captain')

        if not all([barangay_location, barangay_hotline, barangay_residents, barangay_captain]):
            return jsonify({"success": False, "message": "All barangay information fields are required for officials"}), 400

    # Create user in database
    kwargs = {}
    if role == 'official':
        kwargs = {
            'barangay_location': barangay_location,
            'barangay_hotline': barangay_hotline,
            'barangay_captain': barangay_captain,
            'barangay_residents': barangay_residents
        }

    try:
        user_id = create_user(full_name, password, role, access_code=access_code, **kwargs)

        if user_id:
            response_data = {
                "success": True,
                "message": "User registered successfully",
                "user": {"id": user_id, "full_name": full_name, "role": role}
            }

            # Include barangay info in response if official
            if role == 'official':
                response_data["user"].update({
                    "barangay_hotline": barangay_hotline,
                    "barangay_captain": barangay_captain,
                    "barangay_location": barangay_location,
                    "barangay_residents": barangay_residents
                })

            return jsonify(response_data)
        else:
            return jsonify({"success": False, "message": "Registration failed"}), 500
    except Exception as e:
        print(f"Registration error: {e}")
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"success": False, "message": "A user with this name already exists"}), 400
        return jsonify({"success": False, "message": "Registration failed"}), 500

@app.route("/api/login", methods=["POST"])
def login_api():
    data = request.get_json()
    full_name = data.get('full_name')
    password = data.get('password')
    access_code = data.get('access_code')

    if not full_name or not password or not access_code:
        return jsonify({"success": False, "message": "Full name, password, and access code are required"}), 400

    # Validate access code
    valid_access_codes = {
        "ADMIN123": "Barangay Malitam, Batangas City",
        "BARANGAY456": "Barangay Libjo, Batangas City",
        "OFFICIAL789": "Barangay Sorosoro Karsada, Batangas City"
    }

    # Default barangay info for each access code
    default_barangay_info = {
        "ADMIN123": {
            "barangay_hotline": "123-4567",
            "barangay_captain": "Hon. Maria Santos",
            "barangay_location": "Barangay Malitam, Batangas City",
            "barangay_residents": "2500"
        },
        "BARANGAY456": {
            "barangay_hotline": "234-5678",
            "barangay_captain": "Hon. Juan Dela Cruz",
            "barangay_location": "Barangay Libjo, Batangas City",
            "barangay_residents": "1800"
        },
        "OFFICIAL789": {
            "barangay_hotline": "345-6789",
            "barangay_captain": "Hon. Ana Reyes",
            "barangay_location": "Barangay Sorosoro Karsada, Batangas City",
            "barangay_residents": "3200"
        }
    }

    if access_code not in valid_access_codes:
        return jsonify({"success": False, "message": "Invalid access code"}), 400

    # Verify password and access code against database
    user = verify_password(full_name, password, access_code)

    if user:
        response_data = {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "full_name": user['full_name'],
                "role": user['role'],
                "access_code": user.get('access_code')
            }
        }

        # Get barangay info - use defaults, override with database for officials
        barangay_info = default_barangay_info.get(access_code, {})

        # Get background from barangay_backgrounds table (per access code) - available to all users
        from db_config import get_barangay_background
        background_path = get_barangay_background(access_code)
        if background_path:
            barangay_info["background_path"] = background_path

        # If user is official, try to get additional info from database
        if user['role'] == 'official':
            from db_config import db
            db_barangay_info = db.fetch_one("SELECT * FROM barangay_info WHERE user_id = ?", (user['id'],))
            if db_barangay_info:
                barangay_info = {
                    "barangay_hotline": db_barangay_info['barangay_hotline'],
                    "barangay_captain": db_barangay_info['barangay_captain'],
                    "barangay_location": db_barangay_info['barangay_location'],
                    "barangay_residents": db_barangay_info['barangay_residents']
                }
                # Re-add background if it was overridden
                if background_path:
                    barangay_info["background_path"] = background_path

        # Add barangay info to user response
        response_data["user"].update(barangay_info)

        return jsonify(response_data)
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/api/complaints", methods=["POST"])
def create_complaint_endpoint():
    print("=== COMPLAINT CREATION START ===")

    # Check if this is a multipart form request (with file) or JSON request
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        print("Processing multipart form data (with file)")

        # Handle multipart form data
        user_id = request.form.get('user_id')
        description = request.form.get('description')
        category = request.form.get('category', 'Others')
        location = request.form.get('location')

        print(f"Form data - user_id: {user_id}, description: {description}, category: {category}, location: {location}")

        media_path = None

        # Handle file upload if present
        if 'media' in request.files:
            file = request.files['media']
            print(f"File received: {file.filename}, content_type: {file.content_type}")

            if file.filename != '':
                # Validate file type (images and videos)
                allowed_types = ['image/', 'video/']
                if not any(file.content_type.startswith(t) for t in allowed_types):
                    return jsonify({"success": False, "message": "File must be an image or video"}), 400

                # Validate file size (max 10MB for videos, 5MB for images)
                file_content = file.read()
                file_size = len(file_content)

                max_size = 10 * 1024 * 1024 if file.content_type.startswith('video/') else 5 * 1024 * 1024
                if file_size > max_size:
                    size_mb = max_size / (1024 * 1024)
                    return jsonify({"success": False, "message": f"File size must be less than {size_mb}MB"}), 400

                try:
                    # Create uploads directory if it doesn't exist
                    upload_dir = os.path.join(app.static_folder, 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)

                    # Secure filename and save
                    filename = secure_filename(f"complaint_{user_id}_{int(__import__('time').time())}_{file.filename}")
                    filepath = os.path.join(upload_dir, filename)

                    # Write the file content
                    with open(filepath, 'wb') as f:
                        f.write(file_content)

                    # Generate URL path for frontend
                    media_path = f"/static/uploads/{filename}"
                    print(f"File saved successfully: {media_path}")

                except Exception as e:
                    print(f"File upload error: {e}")
                    return jsonify({"success": False, "message": "Failed to upload file"}), 500
    else:
        print("Processing JSON data (no file)")
        # Handle JSON data (existing functionality)
        data = request.get_json()
        user_id = data.get('user_id')
        description = data.get('description')
        category = data.get('category', 'Others')
        location = data.get('location')
        media_path = None

    if not user_id or not description:
        return jsonify({"success": False, "message": "User ID and description are required"}), 400

    try:
        complaint_id = create_complaint(user_id, description, category, location, media_path)

        if complaint_id:
            print("=== COMPLAINT CREATION SUCCESS ===")
            return jsonify({
                "success": True,
                "message": "Complaint created successfully",
                "complaint_id": complaint_id
            })
        else:
            return jsonify({"success": False, "message": "Failed to create complaint"}), 500
    except Exception as e:
        print(f"Complaint creation error: {e}")
        return jsonify({"success": False, "message": "Failed to create complaint"}), 500

@app.route("/api/complaints/<int:complaint_id>/status", methods=["PUT"])
def update_complaint_status_endpoint(complaint_id):
    data = request.get_json()
    new_status = data.get('status')
    user_id = data.get('user_id')  # For authorization check

    if not new_status or not user_id:
        return jsonify({"success": False, "message": "Status and user ID are required"}), 400

    # Validate status - accept proper case to match database schema
    valid_statuses = ['Pending', 'In Progress', 'Resolved']
    if new_status not in valid_statuses:
        return jsonify({"success": False, "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    # Check if user is an official
    from db_config import get_user_by_id
    user = get_user_by_id(user_id)
    if not user or user['role'] != 'official':
        return jsonify({"success": False, "message": "Only barangay officials can update complaint status"}), 403

    try:
        result = update_complaint_status(complaint_id, new_status)

        if result > 0:
            return jsonify({
                "success": True,
                "message": f"Complaint status updated to '{new_status}'"
            })
        else:
            return jsonify({"success": False, "message": "Complaint not found or update failed"}), 404
    except Exception as e:
        print(f"Status update error: {e}")
        return jsonify({"success": False, "message": "Failed to update complaint status"}), 500

@app.route("/api/complaints/<int:complaint_id>", methods=["DELETE"])
def delete_complaint_endpoint(complaint_id):
    user_id = request.args.get('user_id')  # For authorization check

    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400

    # Check if user is an official
    from db_config import get_user_by_id
    user = get_user_by_id(user_id)
    if not user or user['role'] != 'official':
        return jsonify({"success": False, "message": "Only barangay officials can delete complaints"}), 403

    try:
        result = delete_complaint(complaint_id)

        if result > 0:
            return jsonify({
                "success": True,
                "message": "Complaint deleted successfully"
            })
        else:
            return jsonify({"success": False, "message": "Complaint not found or deletion failed"}), 404
    except Exception as e:
        print(f"Deletion error: {e}")
        return jsonify({"success": False, "message": "Failed to delete complaint"}), 500

@app.route("/api/barangay/update", methods=["PUT"])
def update_barangay_info():
    data = request.get_json()
    user_id = data.get('user_id')
    barangay_location = data.get('barangay_location')
    barangay_hotline = data.get('barangay_hotline')
    barangay_captain = data.get('barangay_captain')
    barangay_residents = data.get('barangay_residents')

    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400

    # Check if user is an official
    from db_config import get_user_by_id
    user = get_user_by_id(user_id)
    if not user or user['role'] != 'official':
        return jsonify({"success": False, "message": "Only barangay officials can update barangay information"}), 403

    # Validate required fields
    if not all([barangay_location, barangay_hotline, barangay_captain, barangay_residents]):
        return jsonify({"success": False, "message": "All barangay information fields are required"}), 400

    try:
        from db_config import db

        # Check if barangay_info record exists for this user
        existing = db.fetch_one("SELECT id FROM barangay_info WHERE user_id = ?", (user_id,))

        if existing:
            # Update existing record
            db.execute_query("""
                UPDATE barangay_info
                SET barangay_location = ?, barangay_hotline = ?, barangay_captain = ?, barangay_residents = ?
                WHERE user_id = ?
            """, (barangay_location, barangay_hotline, barangay_captain, barangay_residents, user_id))
        else:
            # Insert new record
            db.execute_query("""
                INSERT INTO barangay_info (user_id, barangay_location, barangay_hotline, barangay_captain, barangay_residents)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, barangay_location, barangay_hotline, barangay_captain, barangay_residents))

        return jsonify({
            "success": True,
            "message": "Barangay information updated successfully"
        })
    except Exception as e:
        print(f"Barangay update error: {e}")
        return jsonify({"success": False, "message": "Failed to update barangay information"}), 500

@app.route("/api/barangay/background", methods=["POST"])
def upload_background_image():
    print("=== BACKGROUND UPLOAD START ===")

    # Log all form data
    print(f"Form data keys: {list(request.form.keys())}")
    print(f"Files keys: {list(request.files.keys())}")

    user_id = request.form.get('user_id')
    print(f"User ID: {user_id}")

    if not user_id:
        print("ERROR: User ID is required")
        return jsonify({"success": False, "message": "User ID is required"}), 400

    # Check if user is an official
    from db_config import get_user_by_id
    print(f"Checking user with ID: {user_id}")
    user = get_user_by_id(user_id)
    print(f"User found: {user}")

    if not user:
        print("ERROR: User not found")
        return jsonify({"success": False, "message": "User not found"}), 404

    if user['role'] != 'official':
        print(f"ERROR: User role is {user['role']}, not official")
        return jsonify({"success": False, "message": "Only barangay officials can upload background images"}), 403

    print("User is authorized (official)")

    # Check if file is provided
    if 'background_image' not in request.files:
        print("ERROR: No file provided in request.files")
        return jsonify({"success": False, "message": "No file provided"}), 400

    file = request.files['background_image']
    print(f"File object: {file}")
    print(f"File filename: {file.filename}")
    print(f"File content_type: {file.content_type}")

    if file.filename == '':
        print("ERROR: No file selected (empty filename)")
        return jsonify({"success": False, "message": "No file selected"}), 400

    # Validate file type
    if not file.content_type.startswith('image/'):
        print(f"ERROR: Invalid file type: {file.content_type}")
        return jsonify({"success": False, "message": "File must be an image"}), 400

    print("File type validated")

    # Validate file size (max 5MB) - read file content to check size
    try:
        file_content = file.read()
        file_size = len(file_content)
        print(f"File size: {file_size} bytes")

        if file_size > 5 * 1024 * 1024:
            print("ERROR: File too large")
            return jsonify({"success": False, "message": "File size must be less than 5MB"}), 400

        print("File size validated")
    except Exception as e:
        print(f"ERROR reading file content: {e}")
        return jsonify({"success": False, "message": "Failed to read file"}), 400

    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.static_folder, 'uploads')
        print(f"Upload directory: {upload_dir}")
        print(f"Static folder: {app.static_folder}")

        os.makedirs(upload_dir, exist_ok=True)
        print("Upload directory created/verified")

        # Secure filename and save
        filename = secure_filename(f"background_{user_id}_{file.filename}")
        filepath = os.path.join(upload_dir, filename)
        print(f"Final filename: {filename}")
        print(f"Full filepath: {filepath}")

        # Write the file content
        with open(filepath, 'wb') as f:
            f.write(file_content)

        print("File written successfully")

        # Verify file was written
        if os.path.exists(filepath):
            print(f"File exists at: {filepath}")
        else:
            print("ERROR: File was not written")

        # Generate URL path for frontend
        background_path = f"/static/uploads/{filename}"
        print(f"Background path: {background_path}")

        # Update database - now per access code instead of per user
        from db_config import set_barangay_background
        print("Updating database...")

        # Update background for this access code (shared across all officials of this barangay)
        result = set_barangay_background(user['access_code'], background_path, user_id)
        print(f"Update result: {result}")

        print("Database updated successfully")
        print("=== BACKGROUND UPLOAD SUCCESS ===")

        return jsonify({
            "success": True,
            "message": "Background image uploaded successfully",
            "background_path": background_path
        })
    except Exception as e:
        print(f"Background upload error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "message": "Failed to upload background image"}), 500

# Comments API endpoints
@app.route("/api/complaints/<int:complaint_id>/comments", methods=["GET"])
def get_comments(complaint_id):
    """Get all comments for a specific complaint"""
    try:
        comments = get_comments_for_complaint(complaint_id)
        # Format comments for frontend compatibility
        formatted_comments = []
        for comment in comments:
            formatted_comments.append({
                "id": comment["id"],
                "author": comment["author_name"],
                "text": comment["comment_text"],
                "time_ago": "Just now"  # For now, use simple time ago
            })
        return jsonify(formatted_comments)
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({"success": False, "message": "Failed to fetch comments"}), 500

@app.route("/api/complaints/<int:complaint_id>/comment", methods=["POST"])
def add_comment_endpoint(complaint_id):
    """Add a comment to a complaint"""
    data = request.get_json()
    user_id = data.get('user_id')
    text = data.get('text')  # Changed from comment_text to text to match frontend

    if not user_id or not text:
        return jsonify({"success": False, "message": "User ID and text are required"}), 400

    if not text.strip():
        return jsonify({"success": False, "message": "Comment text cannot be empty"}), 400

    try:
        comment_id = add_comment(complaint_id, user_id, text.strip())

        if comment_id:
            return jsonify({
                "success": True,
                "message": "Comment added successfully",
                "comment_id": comment_id
            })
        else:
            return jsonify({"success": False, "message": "Failed to add comment"}), 500
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({"success": False, "message": "Failed to add comment"}), 500

@app.route("/api/complaints/<int:complaint_id>/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment_endpoint(complaint_id, comment_id):
    """Delete a comment from a complaint"""
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400

    try:
        result = delete_comment(comment_id, user_id)

        if result > 0:
            return jsonify({
                "success": True,
                "message": "Comment deleted successfully"
            })
        else:
            return jsonify({"success": False, "message": "Comment not found or you don't have permission to delete it"}), 404
    except Exception as e:
        print(f"Error deleting comment: {e}")
        return jsonify({"success": False, "message": "Failed to delete comment"}), 500

# Likes API endpoints
@app.route("/api/complaints/<int:complaint_id>/like", methods=["POST"])
def toggle_like_endpoint(complaint_id):
    """Toggle like for a complaint"""
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400

    try:
        liked = toggle_like(complaint_id, user_id)

        return jsonify({
            "success": True,
            "message": f"Complaint {'liked' if liked else 'unliked'} successfully",
            "liked": liked
        })
    except Exception as e:
        print(f"Error toggling like: {e}")
        return jsonify({"success": False, "message": "Failed to toggle like"}), 500

@app.route("/api/complaints/<int:complaint_id>/likes", methods=["GET"])
def get_likes_count_endpoint(complaint_id):
    """Get the number of likes for a complaint"""
    try:
        likes_count = get_likes_count(complaint_id)
        return jsonify({"likes": likes_count})
    except Exception as e:
        print(f"Error fetching likes count: {e}")
        return jsonify({"success": False, "message": "Failed to fetch likes count"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
