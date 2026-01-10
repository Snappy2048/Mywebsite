import os
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, session
from psycopg2.extras import RealDictCursor
from connection import create_connection
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
# new one
app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.before_request
def require_login():
    allowed_routes = ['login', 'index', 'static', 'images', 'uploads', 'home', 'home_games', 'home_projects',
                      'home_blogs', 'blog_details']
    if 'user' not in session and request.endpoint not in allowed_routes:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('index'))


@app.route('/')
def index():
    conn = create_connection()
    if not conn:
        return "Database Connection Error. Check console.", 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM profile WHERE id = 1")
        profile = cur.fetchone()
        cur.execute("SELECT * FROM games ORDER BY created_at DESC")
        games = cur.fetchall()
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
        projects = cur.fetchall()
        cur.execute("SELECT * FROM products ORDER BY created_at DESC")
        products = cur.fetchall()
        cur.execute("SELECT * FROM blogs ORDER BY created_at DESC")
        blogs = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        profile, games, projects, products, blogs = {}, [], [], [], []
    finally:
        cur.close()
        conn.close()
    return render_template('home/index.html',
                           profile=profile,
                           games=games,
                           projects=projects,
                           products=products,
                           blogs=blogs)


@app.route('/home/games')
def home_games():
    conn = create_connection()
    if not conn:
        return "Database Connection Error. Check console.", 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM profile WHERE id = 1")
        profile = cur.fetchone()
        cur.execute("SELECT * FROM games ORDER BY created_at DESC")
        games = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        profile, games = {}, []
    finally:
        cur.close()
        conn.close()
    return render_template('home/games.html', profile=profile, games=games)


@app.route('/home/projects')
def home_projects():
    conn = create_connection()
    if not conn:
        return "Database Connection Error. Check console.", 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM profile WHERE id = 1")
        profile = cur.fetchone()
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
        projects = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        profile, projects = {}, []
    finally:
        cur.close()
        conn.close()
    return render_template('home/projects.html', profile=profile, projects=projects)


@app.route('/home/blogs')
def home_blogs():
    conn = create_connection()
    if not conn:
        return "Database Connection Error. Check console.", 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM profile WHERE id = 1")
        profile = cur.fetchone()
        cur.execute("SELECT * FROM blogs ORDER BY created_at DESC")
        blogs = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        profile, blogs = {}, []
    finally:
        cur.close()
        conn.close()
    return render_template('home/blogs.html', profile=profile, blogs=blogs)


@app.route('/home/blog/<int:id>')
def blog_details(id):
    conn = create_connection()
    if not conn:
        return "Database Connection Error. Check console.", 500
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM profile WHERE id = 1")
        profile = cur.fetchone()

        # Fetch the specific blog
        cur.execute("SELECT * FROM blogs WHERE id = %s", (id,))
        blog = cur.fetchone()

        # Fetch other blogs for the sidebar, excluding current one
        cur.execute("SELECT * FROM blogs WHERE id != %s ORDER BY created_at DESC", (id,))
        other_blogs = cur.fetchall()

        if not blog:
            flash("Blog post not found.", "warning")
            return redirect(url_for('home_blogs'))

    except Exception as e:
        print(f"Error fetching data: {e}")
        profile, blog, other_blogs = {}, None, []
    finally:
        cur.close()
        conn.close()

    return render_template('home/detailed_blog.html', profile=profile, blog=blog, other_blogs=other_blogs)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM login WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        if user:
            user_id = user[0]
            db_username = user[1]
            db_password_hash = user[2]
            if check_password_hash(db_password_hash, password):
                session['user'] = db_username
                session['user_id'] = user_id
                flash('Login successful! Welcome back.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password. Please try again.222222', 'danger')
        else:
            flash('Invalid username or password. Please try again.00111111', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/profile/<int:user_id>')
def get_profile(user_id):
    conn = create_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM profile WHERE id = %s", (user_id,))
    profile = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(profile)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = create_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT 
                l.username, 
                p.name, 
                p.about, 
                p.avatar, 
                p.skills, 
                p.hobbies
            FROM login l
            LEFT JOIN profile p ON l.id = p.login_id
            WHERE l.id = %s
        """
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        cur.execute("SELECT COUNT(*) as count FROM blogs")
        blog_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) as count FROM games")
        game_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) as count FROM projects")
        project_count = cur.fetchone()['count']
        counts = {
            'blogs': blog_count,
            'games': game_count,
            'projects': project_count
        }
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        user = {}
        counts = {'blogs': 0, 'games': 0, 'projects': 0}
    finally:
        cur.close()
        conn.close()
    return render_template('dashboard.html', user=user, counts=counts)


@app.route('/games')
def games():
    conn = create_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM games ORDER BY created_at DESC')
    games_data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('games.html', games=games_data)


@app.route('/add_game', methods=['POST'])
def add_game():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form.get('link')
        embed_code = request.form.get('embed_code')
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        conn = create_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO games (title, description, image, link, embed_code) VALUES (%s, %s, %s, %s, %s)',
                (title, description, image_filename, link, embed_code)
            )
            conn.commit()
            flash('Game added successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding game: {e}', 'error')
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('games'))


@app.route('/edit_game/<int:id>', methods=['POST'])
def edit_game(id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form.get('link')
        embed_code = request.form.get('embed_code')
        conn = create_connection()
        cur = conn.cursor()
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute(
                'UPDATE games SET title = %s, description = %s, link = %s, image = %s, embed_code = %s WHERE id = %s',
                (title, description, link, filename, embed_code, id)
            )
        else:
            cur.execute(
                'UPDATE games SET title = %s, description = %s, link = %s, embed_code = %s WHERE id = %s',
                (title, description, link, embed_code, id)
            )
        conn.commit()
        cur.close()
        conn.close()
        flash('Game updated successfully!', 'success')
        return redirect(url_for('games'))


@app.route('/delete_game/<int:id>', methods=['POST'])
def delete_game(id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM games WHERE id = %s', (id,))
        conn.commit()
        flash('Game deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error deleting game.', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('games'))


@app.route('/blogs')
def blogs():
    conn = create_connection()
    if not conn:
        flash('Database connection failed.', 'error')
        return render_template('blogs.html', blogs=[])
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, content, thumbnail, created_at, youtube_link FROM blogs ORDER BY created_at DESC")
            rows = cur.fetchall()
            formatted_blogs = []
            for row in rows:
                formatted_blogs.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'thumbnail': row[3],
                    'created_at': row[4],
                    'youtube_link': row[5]
                })
            return render_template('blogs.html', blogs=formatted_blogs)
    except Exception as e:
        print(e)
        flash('Error fetching blogs.', 'error')
        return render_template('blogs.html', blogs=[])
    finally:
        conn.close()


@app.route('/add_blog', methods=['POST'])
def add_blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        youtube_link = request.form.get('youtube_link')

        if not title or not content:
            flash('Title and Content are required!', 'error')
            return redirect(url_for('blogs'))

        thumbnail_path = ""
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                thumbnail_path = f"uploads/{filename}"
            elif file.filename != "":
                flash('Invalid thumbnail format.', 'error')
                return redirect(url_for('blogs'))

        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO blogs (title, content, thumbnail, youtube_link)
                        VALUES (%s, %s, %s, %s)
                    """, (title, content, thumbnail_path, youtube_link))
                    conn.commit()
                    flash('Blog published successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Failed to publish blog.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('blogs'))


@app.route('/edit_blog/<int:id>', methods=['POST'])
def edit_blog(id):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        youtube_link = request.form.get('youtube_link')

        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if 'thumbnail' in request.files and request.files['thumbnail'].filename != '':
                        file = request.files['thumbnail']
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            thumbnail_path = f"uploads/{filename}"
                            cur.execute("""
                                UPDATE blogs SET title=%s, content=%s, thumbnail=%s, youtube_link=%s WHERE id=%s
                            """, (title, content, thumbnail_path, youtube_link, id))
                        else:
                            flash('Invalid file format.', 'error')
                            return redirect(url_for('blogs'))
                    else:
                        cur.execute("""
                            UPDATE blogs SET title=%s, content=%s, youtube_link=%s WHERE id=%s
                        """, (title, content, youtube_link, id))
                    conn.commit()
                    flash('Blog updated successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Error updating blog.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('blogs'))


@app.route('/delete_blog/<int:id>', methods=['POST'])
def delete_blog(id):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM blogs WHERE id = %s", (id,))
                conn.commit()
                flash('Blog deleted successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error deleting blog.', 'danger')
        finally:
            conn.close()
    return redirect(url_for('blogs'))


@app.route('/products')
def products():
    conn = create_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('products.html', products=[])
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description, price, image, created_at FROM products ORDER BY created_at DESC")
            rows = cur.fetchall()
            formatted_products = []
            for row in rows:
                formatted_products.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': row[3],
                    'image': row[4],
                    'created_at': row[5]
                })
            return render_template('products.html', products=formatted_products)
    except Exception as e:
        print(e)
        flash('Error fetching products.', 'error')
        return render_template('products.html', products=[])
    finally:
        conn.close()


@app.route('/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form.get('price')
        if not name:
            flash('Product Name is required!', 'error')
            return redirect(url_for('products'))
        image_path = ""
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"uploads/{filename}"
            else:
                flash('Invalid image format.', 'error')
                return redirect(url_for('products'))
        else:
            flash('Product image is required.', 'error')
            return redirect(url_for('products'))
        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO products (name, description, price, image)
                        VALUES (%s, %s, %s, %s)
                    """, (name, description, price if price else None, image_path))
                    conn.commit()
                    flash('Product added successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Failed to add product.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('products'))


@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form.get('price')
        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if 'image' in request.files and request.files['image'].filename != '':
                        file = request.files['image']
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            image_path = f"uploads/{filename}"
                            cur.execute("""
                                UPDATE products SET name=%s, description=%s, price=%s, image=%s WHERE id=%s
                            """, (name, description, price if price else None, image_path, id))
                        else:
                            flash('Invalid file format.', 'error')
                            return redirect(url_for('products'))
                    else:
                        cur.execute("""
                            UPDATE products SET name=%s, description=%s, price=%s WHERE id=%s
                        """, (name, description, price if price else None, id))
                    conn.commit()
                    flash('Product updated successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Error updating product.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('products'))


@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = %s", (id,))
                conn.commit()
                flash('Product deleted successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error deleting product.', 'danger')
        finally:
            conn.close()
    return redirect(url_for('products'))


@app.route('/projects')
def projects():
    conn = create_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('projects.html', projects=[])
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, description, image, github_link, created_at FROM projects ORDER BY created_at DESC")
            rows = cur.fetchall()
            formatted_projects = []
            for row in rows:
                formatted_projects.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'image': row[3],
                    'github_link': row[4],
                    'created_at': row[5]
                })
            return render_template('projects.html', projects=formatted_projects)
    except Exception as e:
        print(e)
        flash('Error fetching projects.', 'error')
        return render_template('projects.html', projects=[])
    finally:
        conn.close()


@app.route('/add_project', methods=['POST'])
def add_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        github_link = request.form['github_link']
        if not title:
            flash('Project Title is required!', 'error')
            return redirect(url_for('projects'))
        image_path = ""
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"uploads/{filename}"
            else:
                flash('Invalid image format.', 'error')
                return redirect(url_for('projects'))
        else:
            flash('Project image is required.', 'error')
            return redirect(url_for('projects'))
        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO projects (title, description, image, github_link)
                        VALUES (%s, %s, %s, %s)
                    """, (title, description, image_path, github_link))
                    conn.commit()
                    flash('Project added successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Failed to add project.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('projects'))


@app.route('/edit_project/<int:id>', methods=['POST'])
def edit_project(id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        github_link = request.form['github_link']
        conn = create_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if 'image' in request.files and request.files['image'].filename != '':
                        file = request.files['image']
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            image_path = f"uploads/{filename}"
                            cur.execute("""
                                UPDATE projects SET title=%s, description=%s, image=%s, github_link=%s WHERE id=%s
                            """, (title, description, image_path, github_link, id))
                        else:
                            flash('Invalid file format.', 'error')
                            return redirect(url_for('projects'))
                    else:
                        cur.execute("""
                            UPDATE projects SET title=%s, description=%s, github_link=%s WHERE id=%s
                        """, (title, description, github_link, id))
                    conn.commit()
                    flash('Project updated successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(f"Error: {e}")
                flash('Error updating project.', 'danger')
            finally:
                conn.close()
    return redirect(url_for('projects'))


@app.route('/delete_project/<int:id>', methods=['POST'])
def delete_project(id):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM projects WHERE id = %s", (id,))
                conn.commit()
                flash('Project deleted successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error deleting project.', 'danger')
        finally:
            conn.close()
    return redirect(url_for('projects'))


@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    conn = create_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT 
            l.id as login_id, 
            l.username, 
            p.name, 
            p.about, 
            p.avatar, 
            p.skills, 
            p.hobbies
        FROM login l
        LEFT JOIN profile p ON l.id = p.login_id
        WHERE l.id = %s
    """
    cur.execute(query, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        flash('User not found', 'error')
        return redirect('/')
    return render_template('profile.html', user=user)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    username = request.form['username']
    name = request.form['name']
    about = request.form['about']
    skills = request.form['skills']
    hobbies = request.form['hobbies']
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE login SET username = %s WHERE id = %s", (username, user_id))
        avatar_filename = None
        if 'avatar' in request.files and request.files['avatar'].filename != '':
            file = request.files['avatar']
            filename = secure_filename(f"u{user_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            avatar_filename = filename
        cur.execute("SELECT id FROM profile WHERE login_id = %s", (user_id,))
        exists = cur.fetchone()
        if exists:
            if avatar_filename:
                cur.execute("""
                    UPDATE profile 
                    SET name=%s, about=%s, skills=%s, hobbies=%s, avatar=%s 
                    WHERE login_id=%s
                """, (name, about, skills, hobbies, avatar_filename, user_id))
            else:
                cur.execute("""
                    UPDATE profile 
                    SET name=%s, about=%s, skills=%s, hobbies=%s 
                    WHERE login_id=%s
                """, (name, about, skills, hobbies, user_id))
        else:
            cur.execute("""
                INSERT INTO profile (login_id, name, about, skills, hobbies, avatar)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, name, about, skills, hobbies, avatar_filename))
        conn.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating profile: {e}', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('profile'))


@app.route('/change_password', methods=['POST'])
def change_password():
    user_id = session.get('user_id')
    current_pass = request.form['current_password']
    new_pass = request.form['new_password']
    confirm_pass = request.form['confirm_password']
    if new_pass != confirm_pass:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))
    conn = create_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT password_hash FROM login WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if user and check_password_hash(user['password_hash'], current_pass):
        hashed_new = generate_password_hash(new_pass)
        cur.execute("UPDATE login SET password_hash = %s WHERE id = %s", (hashed_new, user_id))
        conn.commit()
        flash('Password changed successfully!', 'success')
    else:
        flash('Incorrect current password.', 'error')
    cur.close()
    conn.close()
    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(debug=True, port=8089, host='0.0.0.0')