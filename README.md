# ⛪ PHM-ARCC Church Management System

A professional, high-fidelity church management platform designed for the **PHM-ARCC Iyumbu Church** in Dodoma. This system streamlines communication, donations, sermons, and member engagement.

---

## ✨ Key Features

- **🌍 Industry-Standard Localization**: Seamlessly toggle between **English** and **Kiswahili** across the entire platform.
- **📱 Smart SMS Notifications**: Integrated with **Twilio** for real-time mobile broadcasts to church members.
- **📊 Robust Dashboards**: Specialized interfaces for **Pastors** (admin/management) and **Members** (giving/content).
- **📻 Content Player**: Centralized hub for church sermons, series, and community media.
- **💸 Giving & Donations**: Track church campaigns and manage member donation history.
- **🏢 Professional UI**: Modern, glassmorphism-inspired design with a curated premium color palette.

---

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **SMS Infrastructure**: Twilio REST API
- **Design System**: Vanilla CSS (Handcrafted Premium UI)
- **Icons**: Font Awesome 6 & Lucide-style SVG

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.8+
- [Git](https://git-scm.com/)

### 2. Installation
Clone the project and set up your virtual environment:
```bash
# Clone the repository
git clone https://your-repo-url/church_system.git
cd church_system

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create your local environment file:
```bash
cp .env.example .env
```
Fill in the [**.env**](file:///home/mlenda/workstation/church_system/.env) file with your secret key, database settings, and Twilio credentials.

### 4. Database Setup & Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Running the Application
```bash
python manage.py runserver 0.0.0.0:8000
```
Visit the app at: `http://localhost:8000`

---

## 📖 Technical Documentation

Detailed guides for specific components:
- 📲 [**SMS Setup Guide (Twilio)**](file:///home/mlenda/workstation/church_system/docs/SMS_SETUP.md)
- 🖼️ [**Logo & Branding Setup**](file:///home/mlenda/workstation/church_system/docs/LOGO_SETUP.md)
- 🌍 [**Localization Guide (Multi-language)**](file:///home/mlenda/workstation/church_system/docs/LOCALIZATION.md)

---

## 👥 Contributors
- **Development Team**: Antigravity AI
- **PHM-ARCC Church Administration**

---
*Serving the community with excellence.*
