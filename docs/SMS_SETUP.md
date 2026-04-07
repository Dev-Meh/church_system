# Production Setup: SMS & Database

This guide explains how to configure the PHM-ARCC Church Management System for a live production environment.

## 1. Twilio SMS Setup

To enable real-time SMS notifications for members:

1.  **Get Twilio Credentials**: Obtain your `Account SID` and `Auth Token` from the [Twilio Console](https://console.twilio.com/).
2.  **Purchase a Number**: Buy a Twilio phone number that supports SMS.
3.  **Set Geo-Permissions**: In Twilio Console, ensure **Tanzania** is enabled under Messaging > Settings > Geo-Permissions.
4.  **Update .env**:
    ```bash
    TWILIO_ACCOUNT_SID=your_sid
    TWILIO_AUTH_TOKEN=your_token
    TWILIO_PHONE_NUMBER=your_number
    SMS_DEVELOPMENT_MODE=False
    ```

## 2. PostgreSQL Database Setup

For production, we recommend **PostgreSQL** over SQLite.

1.  **Install PostgreSQL** on your server.
2.  **Create a Database** (e.g., `church_db`).
3.  **Update .env**:
    ```bash
    DB_ENGINE=django.db.backends.postgresql
    DB_NAME=church_db
    DB_USER=your_user
    DB_PASSWORD=your_password
    DB_HOST=localhost
    DB_PORT=5432
    ```
4.  **Migrate**:
    ```bash
    python manage.py migrate
    ```

---
*PHM-ARCC Church Management System*
