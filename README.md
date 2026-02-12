# 📸 SnapStream - Secure Cloud Video Gallery

<img width="1919" height="928" alt="image" src="https://github.com/user-attachments/assets/6cee9401-2e03-436c-97da-6e71baa2ea2d" />
(https://via.placeholder.com/1000x300?text=SnapStream+Secure+Cloud+Gallery)
**SnapStream** is a secure, cloud-native video sharing platform built with Python and Flask. It allows users to upload, manage, and explore video content in a secure environment. The application is deployed on AWS EC2, utilizing Nginx as a reverse proxy and Gunicorn as the application server, ensuring high performance and scalability.

---

## 📑 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation (Local)](#-installation-local)
- [Deployment (AWS EC2)](#-deployment-aws-ec2)
- [Usage](#-usage)
- [Screenshots](#-screenshots)

---

## 🚀 Features

### 🔒 **Secure Authentication**
- **User Signup/Login:** Robust session management using `Flask-Login`.
- **Private Sessions:** Users must authenticate to access upload and studio features.
- **Profile Management:** Secure password changes and profile picture updates.

### 🌎 **Explore & Community**
- **Public Feed:** A responsive "Explore" page visible to all visitors (no login required).
- **Community Content:** View videos uploaded by other users in a dynamic grid layout.
- **Fast Streaming:** Optimized media delivery from cloud storage.

### 🎬 **Creator Studio**
- **Personal Dashboard:** A private "Studio" view to manage your own uploaded content.
- **Upload Manager:** Drag-and-drop video upload with custom thumbnails and titles.
- **Media Management:** Easy interface to track your portfolio.

---

## 🛠 Tech Stack

| Category | Technologies |
|:--- |:--- |
| **Backend** | Python 3.9, Flask (Microframework) |
| **Server** | Gunicorn (WSGI), Nginx (Reverse Proxy) |
| **Database** | AWS DynamoDB (NoSQL) |
| **Storage** | AWS S3 (Object Storage) |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap (Responsive) |
| **Infrastructure** | AWS EC2 (Amazon Linux 2023) |
| **Dev Tools** | VS Code, Git, SSH |

---

## 🏗 Architecture

The application follows a standard **WSGI** deployment pattern on AWS:

1.  **Client Request** → User visits the Public IP.
2.  **Nginx (Port 80)** → Acts as the Reverse Proxy and handles static files.
3.  **Gunicorn (Port 8000)** → Serves the Flask Application.
4.  **Flask App** → Handles logic, routes, and talks to AWS Services.
5.  **AWS Services** →
    * **DynamoDB:** Stores User Metadata & Video Details.
    * **S3:** Stores actual Video Files & Thumbnails.

---

## 💻 Installation (Local)

Follow these steps to run SnapStream on your local machine.

### Prerequisites
* Python 3.8+
* AWS Credentials (if connecting to real AWS services)

### Steps
1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/SnapStream.git](https://github.com/your-username/SnapStream.git)
    cd SnapStream
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file or update `config.py` with your AWS details:
    ```python
    SECRET_KEY = 'your_secret_key'
    AWS_REGION = 'us-east-1'
    DYNAMO_TABLE_VIDEO = 'SnapStream-Videos'
    ```

5.  **Run the App**
    ```bash
    python application.py
    ```
    Visit `http://localhost:5000` in your browser.

---

## ☁ Deployment (AWS EC2)

This project is deployed on an **AWS EC2 (Amazon Linux 2023)** instance.

### Summary of Deployment Steps:
1.  **Provision:** Launch EC2 instance and configure Security Groups (Allow Ports 80, 22).
2.  **Setup:** Install Python 3, Pip, Nginx, and Git.
    ```bash
    sudo dnf install python3-pip nginx -y
    ```
3.  **Transfer:** Upload code via `scp` or `git clone`.
4.  **Install:** Install requirements inside the server.
    ```bash
    pip3 install -r requirements.txt
    ```
5.  **Nginx Config:** Configure `/etc/nginx/nginx.conf` to proxy pass to localhost:8000.
6.  **Run:** Start Gunicorn in daemon mode.
    ```bash
    gunicorn --bind 0.0.0.0:8000 application:application --daemon
    ```

---

## 📸 Screenshots

| **Home Page** | **Studio Dashboard** |
|:---:|:---:|
| <img width="1919" height="928" alt="image" src="https://github.com/user-attachments/assets/46afc219-5167-4d05-8a9b-09a2de39fe2c" /> | <img width="1919" height="922" alt="image" src="https://github.com/user-attachments/assets/c19e6a76-0f74-4f06-971c-a4cb96bfc9dc" /> |
| *The public landing page* | *Private user dashboard* |

| **Upload Interface** | **Secure Login** |
|:---:|:---:|
| <img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/b5918f90-8bef-4772-a022-b21d65d1cf2d" /> | <img width="1919" height="918" alt="image" src="https://github.com/user-attachments/assets/36f8c813-ad50-445b-890e-2be55023500a" />
| *Video upload modal* | *Authentication screen* |

---


---

### 👤 Author
**Mohammed Moinuddin Shaikh**
* Connect on [LinkedIn]([https://linkedin.com/in/your-profile](https://www.linkedin.com/in/mohammed-moinuddin-shaikh-699ab7259?utm_source=share_via&utm_content=profile&utm_medium=member_android))
* GitHub: [Codesmith-23](https://github.com/Codesmith-23)
