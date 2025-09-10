# Backend Project

This is a backend project built with FastAPI (or your chosen framework). Follow the instructions below to set up and run the project.

---

## 🚀 Getting Started

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/Electrasphere/avaronn-backend.git
```

### 2. Go to project
Change to directory or open it in any code editor , for using CLI
```bash
cd avaronn-backend
```


### 3. Create a virtual environment 
Create a virtual environment and activate it (Optional but Good practice)

Create a virtual environment
```bash
python -m venv venv
```

Activate virtual environment
```bash
venv/Scripts/activate
```


### 4. Install requiremnts
Install requirements from requirements.txt file

```bash
pip install -r requirements.txt
```

### 5. Create a .env file with variables as below

AWS_ACCESS_KEY = "YOUR ACCESS KEY"  
AWS_ACCESS_SECRET_KEY = "YOUR SECRET ACCESS KEY"  
REGION_NAME = "YOUR REGION"  
FILE_UPLOAD_BUCKET = "YOUR S3 BUCKET"  
SERVER = "SERVER NAME i.e DEVELOPMENT1 , DEVELOPMENT , PRODUCTION"  


### 6. Run the Project
Run the main.py file to run project

```bash
python src/main.py
```

OR

```bash
cd src
python main.py
```
