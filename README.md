# CryptChat: A Secure Messaging Platform

Mini Project - I (Real-World Application Development), TYBSc Computer Science.

CryptChat is a small web-based messaging application where users find and message each other by **username** instead of phone number. It is an educational project that demonstrates authentication, encrypted message storage, and relational database design.

## Features

- User registration and login/logout with session-based authentication
- Passwords hashed with **bcrypt** (never stored in plain text)
- Username search and connection requests (send, accept, reject, remove)
- Block and unblock users
- One-to-one text messaging between connected users
- Message content encrypted with **AES-256-GCM** before it is stored in MySQL
- Chat history, with new messages fetched every 3 seconds
- Online/offline status based on last activity
- Admin dashboard with account enable/disable and deletion controls
- Parameterized SQL queries and server-side input validation

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Jinja2 templates |
| Backend | Python, Flask |
| Database | MySQL (`mysql-connector-python`) |
| Security | bcrypt, AES-256-GCM (`cryptography`), Flask sessions |
| Tools | VS Code, MySQL Workbench, Git, GitHub |

## Project Structure

```
CryptChat/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── auth.py           # Routes: auth, search, connections, chat
│   ├── admin.py          # Admin login, dashboard, and user management
│   ├── db.py             # MySQL connection helper
│   └── encryption.py     # AES-256-GCM encrypt/decrypt
├── static/               # CSS, JavaScript
├── templates/            # Jinja2 HTML pages, including admin pages
├── tests/                # Manual test scripts
├── docs/                 # Project documentation
├── schema.sql            # Database schema
├── requirements.txt
├── run.py
└── README.md
```

## Setup (Windows)

### 1. Prerequisites
Python 3.10+, MySQL Server, and Git.

### 2. Clone and create a virtual environment
```bash
git clone https://github.com/kuduyash99/CryptChat.git
cd CryptChat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the database
Run `schema.sql` in MySQL Workbench, or from the terminal:
```bash
mysql -u root -p < schema.sql
```
This creates the `cryptchat` database and its four tables: `users`, `messages`, `connection_requests`, `blocks`.

### 4. Configure environment variables
Create a file named `.env` in the project root:

```
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=cryptchat

SECRET_KEY=your_secret_key
MESSAGE_ENCRYPTION_KEY=your_encryption_key
```

Generate the two keys:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```
Use the first output for `SECRET_KEY` and the second for `MESSAGE_ENCRYPTION_KEY`.

> **Important:** `.env` is excluded from Git. Never commit it. If `MESSAGE_ENCRYPTION_KEY` changes, previously stored messages can no longer be decrypted.

### 5. Create an admin account
1. Start the app with `python run.py` and register the account you want to use as an administrator.
2. Stop the app with `Ctrl+C`. In MySQL Workbench, grant that account admin access (replace `your_username` with the registered username):

```sql
UPDATE users SET is_admin = TRUE WHERE username = 'your_username';
```

Only grant this role to trusted accounts. Open the **Admin Login** link on the home page and sign in with that account.

### 6. Run
```bash
python run.py
```
Open http://127.0.0.1:5000 and sign in through the **Admin Login** link.

## Demo: Two Users

1. Register two accounts (for example `alice_01` and `bob_02`), using a normal window for one and a private/incognito window for the other.
2. From one account, search for the other and send a connection request.
3. Accept the request from the other account under **Requests**.
4. Open the chat from **Connections** and exchange messages.

## Security Design

- **Passwords:** bcrypt with a per-password salt.
- **Messages:** AES-256-GCM with a unique random 12-byte nonce per message. Ciphertext and nonce are stored in the database; the key lives only in `.env`.
- **Sessions:** server-side checks on every protected route.
- **CSRF:** state-changing forms are protected with Flask-WTF CSRF tokens.
- **Database access:** parameterized queries only.
- **Secrets:** loaded from environment variables, not hard-coded.

## Limitations

- Encryption and decryption happen on the server, so this is **encrypted storage at rest, not end-to-end encryption**.
- New messages arrive by polling every few seconds, not by WebSockets.
- Runs as a local development server; not production-hardened.
- Login rate limiting is not implemented.

## Author

Yash, TYBSc Computer Science.
