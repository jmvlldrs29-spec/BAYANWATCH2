/**********************************************************
 * BAYANWATCH – FULL FUNCTIONALITY JS
 * - Menu navigation
 * - Theme toggle
 * - Admin panel
 * - Form submissions
 * - Filters and search
 **********************************************************/

/* ================= GLOBAL STATE ================= */

let complaints = [];
let currentComplaints = [];
let filteredComplaints = [];

let currentUser = {
  id: localStorage.getItem("bw_user_id") || 1,
  name: localStorage.getItem("bw_user_name") || "Citizen User",
  role: localStorage.getItem("bw_user_role") || "resident",
  initials: "CU",
  barangay_hotline: localStorage.getItem("bw_brgy_hotline") || "0000",
  barangay_captain: localStorage.getItem("bw_brgy_captain") || "Hon. Juan Mayor",
  barangay_location: localStorage.getItem("bw_brgy_location") || "Barangay Location",
  barangay_residents: localStorage.getItem("bw_brgy_residents") || "0",
  background_path: localStorage.getItem("bw_background_path") || null
};

currentUser.initials = currentUser.name
  .split(/\s+/)
  .map(w => w[0]?.toUpperCase() || "")
  .join("")
  .slice(0, 2);

/* ================= UTILITY FUNCTIONS ================= */

function populateBarangayFilterOptions() {
  const barangayFilter = document.getElementById("barangayFilter");
  if (!barangayFilter) return;

  // Clear existing options
  barangayFilter.innerHTML = '';

  // Add "All barangays" option
  const allOption = document.createElement('option');
  allOption.value = 'all';
  allOption.textContent = 'All barangays';
  barangayFilter.appendChild(allOption);

  // Get unique barangays from current complaints
  const uniqueBarangays = [...new Set(currentComplaints.map(c => c.barangay).filter(b => b && b.trim()))];

  // For officials, add all unique barangays
  if (currentUser.role === 'official') {
    uniqueBarangays.forEach(barangay => {
      const option = document.createElement('option');
      option.value = barangay;
      option.textContent = barangay;
      barangayFilter.appendChild(option);
    });
  } else {
    // For residents, add only their own barangay if it exists
    const userBarangay = currentUser.barangay_location;
    if (userBarangay && uniqueBarangays.includes(userBarangay)) {
      const option = document.createElement('option');
      option.value = userBarangay;
      option.textContent = userBarangay;
      barangayFilter.appendChild(option);
    }
  }
}

function showSection(sectionName) {
  // Hide all sections
  document.querySelectorAll('.page-section').forEach(section => {
    section.classList.remove('is-active');
  });

  // Show selected section
  const targetSection = document.getElementById(`section-${sectionName}`);
  if (targetSection) {
    targetSection.classList.add('is-active');
  }

  // Update menu active state
  document.querySelectorAll('.menu-link').forEach(link => {
    link.classList.remove('active');
  });

  const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
  if (activeLink) {
    activeLink.classList.add('active');
  }
}

function toggleTheme() {
  document.body.classList.toggle('dark-theme');
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.textContent = document.body.classList.contains('dark-theme') ? '☀️' : '🌙';
  }
}

function toggleAdminPanel() {
  const adminPanel = document.getElementById('adminPanel');
  if (adminPanel) {
    adminPanel.classList.toggle('open');
  }
}

/* ================= STATS (GLOBAL, SAFE) ================= */

function updateStats() {
  const statComplaints = document.getElementById("statComplaints");
  const statResolved = document.getElementById("statResolved");
  const statPending = document.getElementById("statPending");

  if (!statComplaints || !statResolved || !statPending) return;

  const total = complaints.length;
  const resolved = complaints.filter(c => c.status === "Resolved").length;
  const pending = complaints.filter(c => c.status === "Pending").length;

  statComplaints.textContent = total;
  statResolved.textContent = resolved;
  statPending.textContent = pending;
}

/* ================= FETCH COMPLAINTS ================= */

async function loadComplaintsFromDB(fetchAll = false) {
  try {
    // Get user's access code from localStorage
    const accessCode = localStorage.getItem('bw_access_code');

    // Determine if we need to fetch all complaints
    // Fetch all if explicitly requested or if user is an official (can see all barangays)
    const shouldFetchAll = fetchAll || currentUser.role === 'official';

    // Include access code in API request to filter complaints by barangay, or fetch all for filtering
    let url;
    if (shouldFetchAll) {
      url = '/api/complaints?fetch_all=true';  // Fetch all complaints for client-side filtering
    } else {
      url = accessCode ? `/api/complaints?access_code=${encodeURIComponent(accessCode)}` : '/api/complaints';
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error("API not ready");

    const data = await res.json();

    if (!Array.isArray(data)) throw new Error("Invalid data");

    currentComplaints = data.map(c => ({
      id: c.id,
      author: c.author || "Anonymous",
      text: c.text || "",
      location: c.location || "",
      category: c.category || "General",
      status: c.status || "Pending",
      timeAgo: c.time_ago || "Just now",
      initials: (c.author || "A").slice(0, 2).toUpperCase(),
      likes: c.likes || 0,
      comments: c.comments || [],  // Use real comments data from backend
      barangay: c.barangay || "",  // Add barangay information for filtering
      mediaUrl: c.mediaUrl || null,
      mediaType: c.mediaType || null
    }));

    complaints = [...currentComplaints]; // Set current display complaints

  } catch (err) {
    console.warn("Using empty complaints (API not ready)");
    currentComplaints = [];
    complaints = [];
  }

  // Populate barangay filter options dynamically
  populateBarangayFilterOptions();

  // Apply current filters
  await applyFilters();
  updateStats();
  renderFeed();
  renderMyComplaints();
}

/* ================= EVENT HANDLERS ================= */

function handleFeedClick(e) {
  const target = e.target;

  // Handle like button clicks
  if (target.classList.contains('like-btn')) {
    e.preventDefault();
    const complaintId = target.getAttribute('data-complaint-id');
    if (complaintId) {
      toggleLike(complaintId);
    }
  }

  // Handle comment button clicks
  if (target.classList.contains('comment-btn')) {
    e.preventDefault();
    const complaintId = target.getAttribute('data-complaint-id');
    if (complaintId) {
      const commentsSection = document.querySelector(`.complaint-comments-section[data-complaint-id="${complaintId}"]`);
      if (commentsSection) {
        commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
      }
    }
  }

  // Handle comment submit button clicks
  if (target.classList.contains('comment-submit-btn')) {
    e.preventDefault();
    const complaintId = target.getAttribute('data-complaint-id');
    const commentInput = document.querySelector(`.comment-input[data-complaint-id="${complaintId}"]`);
    const text = commentInput.value.trim();
    if (!text) {
      alert("Please enter a comment.");
      return;
    }

    // Submit comment
    (async () => {
      try {
        const response = await fetch(`/api/complaints/${complaintId}/comment`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: currentUser.id,
            text: text
          })
        });

        const result = await response.json();

        if (result.success) {
          // Clear input
          commentInput.value = "";
          // Reload complaints to reflect the new comment
          await loadComplaintsFromDB();
        } else {
          alert("Failed to post comment: " + result.message);
        }
      } catch (error) {
        console.error('Error posting comment:', error);
        alert("Error posting comment. Please try again.");
      }
    })();
  }
}

/* ================= RENDER FEED ================= */

function renderFeed() {
  const feed = document.getElementById("feed");
  const feedCount = document.getElementById("feedCount");
  if (!feed) return;

  feed.innerHTML = "";

  const displayComplaints = filteredComplaints.length > 0 ? filteredComplaints : complaints;

  if (displayComplaints.length === 0) {
    feed.innerHTML = `
      <div class="card" style="font-size:0.85rem">
        No complaints yet.
      </div>
    `;
    if (feedCount) feedCount.textContent = "0 complaints";
    return;
  }

  displayComplaints.forEach(c => {
    const card = document.createElement("article");
    card.className = "complaint-card";

    // Add official controls if user is an official
    let officialControls = '';
    if (currentUser.role === 'official') {
      officialControls = `
        <div class="official-controls" style="margin-top: 10px; padding: 10px; border-top: 1px solid #e5e7eb;">
          <div style="display: flex; gap: 10px; align-items: center;">
            <select class="status-select" data-complaint-id="${c.id}" style="padding: 5px; border-radius: 4px; border: 1px solid #d1d5db;">
              <option value="Pending" ${c.status === 'Pending' ? 'selected' : ''}>Pending</option>
              <option value="In Progress" ${c.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
              <option value="Resolved" ${c.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
            </select>
            <button class="btn-update-status" data-complaint-id="${c.id}" style="padding: 5px 10px; background: #0ea5e9; color: white; border: none; border-radius: 4px; cursor: pointer;">Update Status</button>
            <button class="btn-delete-complaint" data-complaint-id="${c.id}" style="padding: 5px 10px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer;">Delete</button>
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="complaint-header">
        <div class="complaint-user">
          <div class="complaint-avatar">${c.initials}</div>
          <div>
            <div class="complaint-user-name">${c.author}</div>
            <div class="complaint-meta">${c.location} • ${c.timeAgo}</div>
          </div>
        </div>
        <span class="status-pill">${c.status}</span>
      </div>

      <div class="complaint-body">${c.text}</div>

      ${c.mediaUrl ? `
        <div class="complaint-media" style="margin: 10px 0;">
          ${c.mediaType === 'image' ?
            `<img src="${c.mediaUrl}" alt="Complaint media" style="max-width: 100%; max-height: 300px; border-radius: 8px; object-fit: cover;">` :
            c.mediaType === 'video' ?
            `<video controls style="max-width: 100%; max-height: 300px; border-radius: 8px;">
               <source src="${c.mediaUrl}" type="video/mp4">
               Your browser does not support the video tag.
             </video>` :
            ''
          }
        </div>
      ` : ''}

      <div class="complaint-extra">
        <span class="complaint-tag">Category: ${c.category}</span>
      </div>

      <div class="complaint-footer">
        <div class="complaint-actions">
          <button class="action-btn like-btn" data-complaint-id="${c.id}">👍 ${c.likes}</button>
          <button class="action-btn comment-btn" data-complaint-id="${c.id}">💬 ${c.comments.length}</button>
        </div>
        <div>For barangay review</div>
      </div>

      <div class="complaint-comments-section" data-complaint-id="${c.id}" style="display: none;">
        ${c.comments.length > 0 ? `
          <div class="complaint-comments" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb;">
            ${c.comments.map(comment => `
              <div class="comment-item" style="margin-bottom: 10px; padding: 8px; background: #f9fafb; border-radius: 6px;">
                <div style="font-weight: 600; font-size: 0.9em; margin-bottom: 4px; color: #374151;">${comment.author || 'Anonymous'}</div>
                <div style="font-size: 0.9em; color: #4b5563;">${comment.text}</div>
                <div style="font-size: 0.8em; color: #6b7280; margin-top: 4px;">${comment.time_ago || 'Just now'}</div>
              </div>
            `).join('')}
          </div>
        ` : ''}

        <div class="comment-form" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb;">
          <div style="display: flex; gap: 10px; align-items: flex-end;">
            <textarea class="comment-input" data-complaint-id="${c.id}" placeholder="Write a comment..." style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; resize: vertical; min-height: 36px; font-size: 0.9em;"></textarea>
            <button class="comment-submit-btn" data-complaint-id="${c.id}" style="padding: 8px 16px; background: #0ea5e9; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em;">Post</button>
          </div>
        </div>
      </div>
      ${officialControls}
    `;

    feed.appendChild(card);
  });

  if (feedCount) {
    feedCount.textContent =
      displayComplaints.length === 1
        ? "1 complaint"
        : `${displayComplaints.length} complaints`;
  }

  // Add event listeners for official controls
  if (currentUser.role === 'official') {
    // Status update buttons
    document.querySelectorAll('.btn-update-status').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const complaintId = e.target.getAttribute('data-complaint-id');
        const select = e.target.previousElementSibling;
        const newStatus = select.value;

        await updateComplaintStatus(complaintId, newStatus);
      });
    });

    // Delete buttons
    document.querySelectorAll('.btn-delete-complaint').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const complaintId = e.target.getAttribute('data-complaint-id');

        if (confirm('Are you sure you want to delete this complaint? This action cannot be undone.')) {
          await deleteComplaint(complaintId);
        }
      });
    });
  }

  // Add event listeners for like and comment buttons using event delegation
  const feedContainer = document.getElementById("feed");
  if (feedContainer) {
    // Remove existing listeners to prevent duplicates
    feedContainer.removeEventListener('click', handleFeedClick);
    feedContainer.addEventListener('click', handleFeedClick);
  }
}

function renderMyComplaints() {
  const myComplaintsList = document.getElementById("myComplaintsList");
  if (!myComplaintsList) return;

  myComplaintsList.innerHTML = "";

  const myComplaints = complaints.filter(c => c.author === currentUser.name);

  if (myComplaints.length === 0) {
    myComplaintsList.innerHTML = `
      <div class="card" style="font-size:0.85rem">
        You haven't filed any complaints yet.
      </div>
    `;
    return;
  }

  myComplaints.forEach(c => {
    const card = document.createElement("article");
    card.className = "complaint-card";

    card.innerHTML = `
      <div class="complaint-header">
        <div class="complaint-user">
          <div class="complaint-avatar">${c.initials}</div>
          <div>
            <div class="complaint-user-name">${c.author}</div>
            <div class="complaint-meta">${c.location} • ${c.timeAgo}</div>
          </div>
        </div>
        <span class="status-pill">${c.status}</span>
      </div>

      <div class="complaint-body">${c.text}</div>

      ${c.mediaUrl ? `
        <div class="complaint-media" style="margin: 10px 0;">
          ${c.mediaType === 'image' ?
            `<img src="${c.mediaUrl}" alt="Complaint media" style="max-width: 100%; max-height: 300px; border-radius: 8px; object-fit: cover;">` :
            c.mediaType === 'video' ?
            `<video controls style="max-width: 100%; max-height: 300px; border-radius: 8px;">
               <source src="${c.mediaUrl}" type="video/mp4">
               Your browser does not support the video tag.
             </video>` :
            ''
          }
        </div>
      ` : ''}

      <div class="complaint-extra">
        <span class="complaint-tag">Category: ${c.category}</span>
      </div>

      <div class="complaint-footer">
        <div class="complaint-actions">
          <button class="action-btn">👍 ${c.likes}</button>
          <button class="action-btn">💬 ${c.comments.length}</button>
        </div>
        <div>For barangay review</div>
      </div>
    `;

    myComplaintsList.appendChild(card);
  });
}

/* ================= FILTERS ================= */

async function applyFilters() {
  const statusFilter = document.getElementById("statusFilter");
  const categoryFilter = document.getElementById("categoryFilter");
  const barangayFilter = document.getElementById("barangayFilter");

  if (!statusFilter || !categoryFilter || !barangayFilter) return;

  const statusValue = statusFilter.value;
  const categoryValue = categoryFilter.value;
  const barangayValue = barangayFilter.value;

  // For officials, fetch all complaints if not already done
  if (currentUser.role === 'official' && currentComplaints.length === 0) {
    try {
      const url = `/api/complaints?fetch_all=true`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          currentComplaints = data.map(c => ({
            id: c.id,
            author: c.author || "Anonymous",
            text: c.text || "",
            location: c.location || "",
            category: c.category || "General",
            status: c.status || "Pending",
            timeAgo: c.time_ago || "Just now",
            initials: (c.author || "A").slice(0, 2).toUpperCase(),
            likes: c.likes || 0,
            comments: [],
            barangay: c.barangay || ""
          }));
        }
      }
    } catch (err) {
      console.warn("Could not fetch all complaints for filtering:", err);
    }
  }

  // Filter from currentComplaints (which contains all complaints if needed)
  filteredComplaints = currentComplaints.filter(c => {
    const statusMatch = statusValue === "all" || c.status === statusValue;
    const categoryMatch = categoryValue === "all" || c.category === categoryValue;
    const barangayMatch = barangayValue === "all" || (c.barangay && c.barangay.trim().toLowerCase() === barangayValue.trim().toLowerCase());
    return statusMatch && categoryMatch && barangayMatch;
  });

  // Update complaints to show filtered results
  complaints = [...filteredComplaints];

  updateStats();
  renderFeed();
  renderMyComplaints();
}

/* ================= FORM HANDLERS ================= */

async function handleComposeSubmit(e) {
  e.preventDefault();

  const text = document.getElementById("complaintText").value.trim();
  const category = document.getElementById("complaintCategory").value;
  const location = document.getElementById("complaintLocation").value.trim();
  const media = document.getElementById("complaintMedia").files[0];

  if (!text || !category || !location) {
    alert("Please fill in all required fields.");
    return;
  }

  try {
    let response;

    // Check if there's a media file attached
    if (media) {
      // Use FormData for multipart upload
      const formData = new FormData();
      formData.append('user_id', currentUser.id.toString());
      formData.append('description', text);
      formData.append('category', category);
      formData.append('location', location);
      formData.append('media', media);

      response = await fetch('/api/complaints', {
        method: 'POST',
        body: formData  // No Content-Type header needed for FormData
      });
    } else {
      // Use JSON for text-only complaints
      response = await fetch('/api/complaints', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: currentUser.id,
          description: text,
          category: category,
          location: location
        })
      });
    }

    const result = await response.json();

    if (result.success) {
      // Clear form
      document.getElementById("complaintText").value = "";
      document.getElementById("complaintCategory").value = "";
      document.getElementById("complaintLocation").value = "";
      document.getElementById("complaintMedia").value = "";

      // Reload complaints from database
      await loadComplaintsFromDB();

      alert("Complaint posted successfully!");
    } else {
      alert("Failed to post complaint: " + result.message);
    }
  } catch (error) {
    console.error('Error posting complaint:', error);
    alert("Error posting complaint. Please try again.");
  }
}

/* ================= OFFICIAL ACTIONS ================= */

async function updateComplaintStatus(complaintId, newStatus) {
  try {
    const response = await fetch(`/api/complaints/${complaintId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status: newStatus,
        user_id: currentUser.id
      })
    });

    const result = await response.json();

    if (result.success) {
      // Reload complaints to reflect the status change
      await loadComplaintsFromDB();
      alert("Complaint status updated successfully!");
    } else {
      alert("Failed to update status: " + result.message);
    }
  } catch (error) {
    console.error('Error updating complaint status:', error);
    alert("Error updating complaint status. Please try again.");
  }
}

async function deleteComplaint(complaintId) {
  try {
    const response = await fetch(`/api/complaints/${complaintId}?user_id=${currentUser.id}`, {
      method: 'DELETE'
    });

    const result = await response.json();

    if (result.success) {
      // Reload complaints to reflect the deletion
      await loadComplaintsFromDB();
      alert("Complaint deleted successfully!");
    } else {
      alert("Failed to delete complaint: " + result.message);
    }
  } catch (error) {
    console.error('Error deleting complaint:', error);
    alert("Error deleting complaint. Please try again.");
  }
}

/* ================= LIKE AND COMMENT FUNCTIONS ================= */

async function toggleLike(complaintId) {
  try {
    const response = await fetch(`/api/complaints/${complaintId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: currentUser.id
      })
    });

    const result = await response.json();

    if (result.success) {
      // Reload complaints to reflect the like change
      await loadComplaintsFromDB();
    } else {
      alert("Failed to toggle like: " + result.message);
    }
  } catch (error) {
    console.error('Error toggling like:', error);
    alert("Error toggling like. Please try again.");
  }
}

async function showCommentsModal(complaintId) {
  // Find the complaint data
  const complaint = complaints.find(c => c.id == complaintId);
  if (!complaint) return;

  // Create modal HTML
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content" style="max-width: 500px; max-height: 80vh; overflow-y: auto;">
      <div class="modal-header">
        <h3>Comments</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
      </div>
      <div class="modal-body">
        <div class="comments-list" style="margin-bottom: 20px;">
          ${complaint.comments.length > 0 ?
            complaint.comments.map(comment => `
              <div class="comment-item" style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="font-weight: bold; margin-bottom: 5px;">${comment.author || 'Anonymous'}</div>
                <div>${comment.text}</div>
                <div style="font-size: 0.8em; color: #6b7280; margin-top: 5px;">${comment.time_ago || 'Just now'}</div>
              </div>
            `).join('') :
            '<div style="text-align: center; color: #6b7280; padding: 20px;">No comments yet.</div>'
          }
        </div>
        <div class="comment-form">
          <textarea id="commentText" placeholder="Write a comment..." style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 4px; resize: vertical; min-height: 80px;"></textarea>
          <button id="submitComment" style="margin-top: 10px; padding: 8px 16px; background: #0ea5e9; color: white; border: none; border-radius: 4px; cursor: pointer;">Post Comment</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Add event listener for comment submission
  const submitBtn = modal.querySelector('#submitComment');
  const commentText = modal.querySelector('#commentText');

  submitBtn.addEventListener('click', async () => {
    const text = commentText.value.trim();
    if (!text) {
      alert("Please enter a comment.");
      return;
    }

    try {
      const response = await fetch(`/api/complaints/${complaintId}/comment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: currentUser.id,
          text: text
        })
      });

      const result = await response.json();

      if (result.success) {
        // Reload complaints to reflect the new comment
        await loadComplaintsFromDB();
        // Close modal
        modal.remove();
      } else {
        alert("Failed to post comment: " + result.message);
      }
    } catch (error) {
      console.error('Error posting comment:', error);
      alert("Error posting comment. Please try again.");
    }
  });

  // Close modal when clicking outside
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

/* ================= ADMIN PANEL ================= */

function populateAdminPanel() {
  const adminUserName = document.getElementById("adminUserName");
  const adminUserRole = document.getElementById("adminUserRole");
  const adminBrgyLocation = document.getElementById("adminBrgyLocation");
  const adminBrgyHotline = document.getElementById("adminBrgyHotline");
  const adminBrgyResidents = document.getElementById("adminBrgyResidents");
  const adminBrgyCaptain = document.getElementById("adminBrgyCaptain");

  if (adminUserName) adminUserName.textContent = currentUser.name;
  if (adminUserRole) adminUserRole.textContent = "Barangay Official";
  if (adminBrgyLocation) adminBrgyLocation.value = currentUser.barangay_location || "";
  if (adminBrgyHotline) adminBrgyHotline.value = currentUser.barangay_hotline || "";
  if (adminBrgyResidents) adminBrgyResidents.value = currentUser.barangay_residents || "";
  if (adminBrgyCaptain) adminBrgyCaptain.value = currentUser.barangay_captain || "";
}

function updateBarangayDisplays() {
  // Update all barangay info displays
  const displays = [
    "brgyHotlineDisplay",
    "brgyHotlineDisplay2",
    "brgyHotlineDisplayRight"
  ];

  displays.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = currentUser.barangay_hotline;
  });

  const captainDisplay = document.getElementById("brgyCaptainDisplay");
  if (captainDisplay) captainDisplay.textContent = currentUser.barangay_captain;

  const infoLines = [
    "brgyInfoLine",
    "brgyInfoLineRight"
  ];

  infoLines.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = `${currentUser.barangay_location} • ${currentUser.barangay_residents} residents`;
  });
}

function applyBackgroundImage(imagePath) {
  if (imagePath) {
    document.body.style.backgroundImage = `url('${imagePath}')`;
    document.body.style.backgroundSize = 'cover';
    document.body.style.backgroundPosition = 'center';
    document.body.style.backgroundRepeat = 'no-repeat';
    document.body.style.backgroundAttachment = 'fixed';
  } else {
    // Reset to default background
    document.body.style.backgroundImage = '';
  }
}

/* ================= PAGE INIT ================= */

document.addEventListener("DOMContentLoaded", () => {
  // Update user info in navbar and sidebar
  const navUserName = document.querySelector(".nav-user-name");
  const navUserRole = document.querySelector(".nav-user-role");
  const navAvatar = document.querySelector(".nav-avatar");
  const userCardHeader = document.querySelector(".user-card-header h2");
  const userRoleLabel = document.getElementById("userRoleLabel");

  if (navUserName) navUserName.textContent = currentUser.name;
  if (navAvatar) navAvatar.textContent = currentUser.initials;
  if (navUserRole)
    navUserRole.textContent =
      currentUser.role === "official"
        ? "Barangay Official"
        : "Citizen";
  if (userCardHeader) userCardHeader.textContent = currentUser.name;
  if (userRoleLabel)
    userRoleLabel.textContent =
      currentUser.role === "official"
        ? "Barangay Official"
        : "Resident";

  // Show admin button for officials
  const adminToggle = document.getElementById("adminToggle");
  if (adminToggle && currentUser.role === "official") {
    adminToggle.style.display = "block";
  }

  // Menu navigation
  document.querySelectorAll('.menu-link').forEach(link => {
    link.addEventListener('click', () => {
      const section = link.getAttribute('data-section');
      showSection(section);
    });
  });

  // Theme toggle
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }

  // Admin panel
  const adminToggleBtn = document.getElementById('adminToggle');
  const adminClose = document.getElementById('adminClose');
  const adminSaveBrgy = document.getElementById('adminSaveBrgy');

  if (adminToggleBtn) {
    adminToggleBtn.addEventListener('click', toggleAdminPanel);
  }

  if (adminClose) {
    adminClose.addEventListener('click', toggleAdminPanel);
  }

  if (adminSaveBrgy) {
    adminSaveBrgy.addEventListener('click', () => {
      // Get form values
      const location = document.getElementById("adminBrgyLocation").value.trim();
      const hotline = document.getElementById("adminBrgyHotline").value.trim();
      const residents = document.getElementById("adminBrgyResidents").value.trim();
      const captain = document.getElementById("adminBrgyCaptain").value.trim();

      // Validate required fields
      if (!location || !hotline || !residents || !captain) {
        alert("All barangay information fields are required.");
        return;
      }

      // Update current user object
      currentUser.barangay_location = location;
      currentUser.barangay_hotline = hotline;
      currentUser.barangay_captain = captain;
      currentUser.barangay_residents = residents;

      // Update localStorage
      localStorage.setItem("bw_brgy_location", location);
      localStorage.setItem("bw_brgy_hotline", hotline);
      localStorage.setItem("bw_brgy_captain", captain);
      localStorage.setItem("bw_brgy_residents", residents);

      // Update displays throughout the page
      updateBarangayDisplays();

      alert("Barangay information updated successfully!");
    });
  }

  // Background image upload functionality
  const adminApplyBg = document.getElementById('adminApplyBg');
  if (adminApplyBg) {
    adminApplyBg.addEventListener('click', async () => {
      const fileInput = document.getElementById('adminBgFile');
      const file = fileInput.files[0];

      if (!file) {
        alert("Please select an image file first.");
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert("Please select a valid image file.");
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert("File size must be less than 5MB.");
        return;
      }

      const formData = new FormData();
      formData.append('background_image', file);
      formData.append('user_id', currentUser.id);

      try {
        const response = await fetch('/api/barangay/background', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (result.success) {
          // Update current user object
          currentUser.background_path = result.background_path;

          // Update localStorage
          localStorage.setItem("bw_background_path", result.background_path);

          // Apply background immediately
          applyBackgroundImage(result.background_path);

          alert("Background image updated successfully!");
        } else {
          alert("Failed to update background: " + result.message);
        }
      } catch (error) {
        console.error('Error uploading background:', error);
        alert("Error uploading background image. Please try again.");
      }
    });
  }

  // Filters
  const statusFilter = document.getElementById("statusFilter");
  const categoryFilter = document.getElementById("categoryFilter");
  const barangayFilter = document.getElementById("barangayFilter");

  // Show barangay filter for all users
  if (barangayFilter) {
    barangayFilter.style.display = 'block';
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', async () => await applyFilters());
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', async () => await applyFilters());
  }

  if (barangayFilter) {
    barangayFilter.addEventListener('change', async () => await applyFilters());
  }

  // Compose form
  const composeForm = document.getElementById("composeForm");
  if (composeForm) {
    composeForm.addEventListener('submit', handleComposeSubmit);
  }

  // Load data
  loadComplaintsFromDB();
  populateAdminPanel();
  updateBarangayDisplays();

  // Apply background image if available
  applyBackgroundImage(currentUser.background_path);
});
