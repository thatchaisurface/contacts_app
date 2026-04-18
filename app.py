from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-secret-key' # required for flash messages
DB = 'contacts.db'

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# --- HELPERS ---

def format_birthday(date_str):
    """Convert '1992-12-20' to '20-DEC-1992'"""
    if not date_str:
        return ''
    try:
        parts = date_str.split('-')
        months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
        day = parts[2]
        month = months[int(parts[1]) - 1]
        year = parts[0]
        return f"{day}-{month}-{year}"
    except:
        return date_str

def truncate_at_word(text, max_chars):
    """Truncate to max_chars at nearest word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.6:
        return truncated[:last_space] + '…'
    return truncated + '…'

# --- PAGES ---

@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'name_asc')
    filter_rel = request.args.get('filter', '').strip()

    conn = get_db_connection()

    # Build WHERE clauses
    conditions = []
    params = []
    if search:
        conditions.append("name LIKE ?")
        params.append(f'%{search}%')
    if filter_rel:
        conditions.append("relationship = ?")
        params.append(filter_rel)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Build ORDER BY
    sort_options = {
        'name_asc':   "name ASC",
        'name_desc':  "name DESC",
        'newest':     "created_at DESC",
        'oldest':     "created_at ASC",
    }
    order_by = sort_options.get(sort, "name ASC")

    # Fetch contacts
    cur = conn.execute(f"SELECT * FROM contacts {where_clause} ORDER BY {order_by}", tuple(params))
    contacts = cur.fetchall()

    # Fetch distinct relationships for the filter dropdown
    relationships = [row['relationship'] for row in conn.execute(
        "SELECT DISTINCT relationship FROM contacts WHERE relationship IS NOT NULL AND relationship != '' ORDER BY relationship"
    ).fetchall()]

    # Fetch notes for all contacts in one query
    all_notes = conn.execute(
        "SELECT id, contact_id, content FROM notes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    # Group notes by contact_id: {contact_id: [note_dict, ...]}
    notes_by_contact = {}
    for row in all_notes:
        cid = row['contact_id']
        if cid not in notes_by_contact:
            notes_by_contact[cid] = []
        notes_by_contact[cid].append({
            'id': row['id'],
            'preview': truncate_at_word(row['content'], 50)
        })

    return render_template('index.html',
        contacts=contacts,
        notes_by_contact=notes_by_contact,
        search=search,
        sort=sort,
        filter_rel=filter_rel,
        relationships=relationships)

@app.route('/contact/<int:contact_id>')
def contact_detail(contact_id):
    conn = get_db_connection()
    contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    rows = conn.execute(
        "SELECT * FROM notes WHERE contact_id = ? ORDER BY created_at DESC",
        (contact_id,)
    ).fetchall()
    notes = [dict(row) for row in rows]
    conn.close()
    if not contact:
        flash("Contact not found.")
        return redirect(url_for('index'))
    return render_template('contact.html', contact=contact, notes=notes)

# --- ACTIONS ---

@app.route('/contact/add', methods=['POST'])
def add_contact():
    name = request.form['name'].strip()
    relationship = request.form.get('relationship', '').strip()
    birthday = request.form.get('birthday', '').strip() or None

    if not name:
        flash("Name is required.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO contacts (name, relationship, birthday, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (name, relationship, birthday, datetime.now().isoformat(), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    flash(f"{name} added.")
    return redirect(url_for('index'))

@app.route('/contact/<int:contact_id>/update', methods=['POST'])
def update_contact(contact_id):
    name = request.form['name'].strip()
    relationship = request.form.get('relationship', '').strip()
    birthday = request.form.get('birthday', '').strip() or None
    last_contacted = request.form.get('last_contacted', '').strip() or None

    conn = get_db_connection()
    conn.execute(
        """UPDATE contacts SET name=?, relationship=?, birthday=?, last_contacted=?, updated_at=?
           WHERE id=?""",
        (name, relationship, birthday, last_contacted, datetime.now().isoformat(), contact_id)
    )
    conn.commit()
    conn.close()
    flash("Contact updated.")
    return redirect(url_for('contact_detail', contact_id=contact_id))

@app.route('/contact/<int:contact_id>/notes/add', methods=['POST'])
def add_note(contact_id):
    content = request.form['content'].strip()
    if not content:
        flash("Note can't be empty.")
        return redirect(url_for('contact_detail', contact_id=contact_id))

    now = datetime.now().isoformat()
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO notes (contact_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (contact_id, content, now, now)
    )
    conn.commit()
    conn.close()
    flash("Note saved.")
    return redirect(url_for('contact_detail', contact_id=contact_id))

@app.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return "Content required", 400

    now = datetime.now().isoformat()
    conn = get_db_connection()
    conn.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
        (content, now, note_id)
    )
    conn.commit()
    row = conn.execute("SELECT updated_at FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return {"updated_at": row['updated_at'] if row else now}

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return "", 204

@app.route('/contact/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM notes WHERE contact_id = ?", (contact_id,))
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()
    flash("Contact deleted.")
    return redirect(url_for('index'))

# Birthday formatter
app.jinja_env.filters['format_birthday'] = format_birthday

# --- RUN ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)