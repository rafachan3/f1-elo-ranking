from main import app, init_db

# Initialize database when the application starts
init_db(app)

if __name__ == "__main__":
    app.run()