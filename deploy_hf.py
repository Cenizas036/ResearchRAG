from huggingface_hub import HfApi, login
import os

HF_TOKEN = os.environ.get("HF_TOKEN", "YOUR_HF_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_KEY")
USERNAME = "Sanket036"
SPACE_NAME = "ResearchRAG-API"
REPO_ID = f"{USERNAME}/{SPACE_NAME}"

# Login
login(token=HF_TOKEN)

api = HfApi()

print(f"Creating space {REPO_ID}...")
try:
    api.create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="docker",
        private=False,
        exist_ok=True
    )
    print("Space created or already exists.")
except Exception as e:
    print(f"Failed to create space: {e}")

print("Adding secrets...")
try:
    api.add_space_secret(
        repo_id=REPO_ID,
        key="OPENAI_API_KEY",
        value=OPENAI_KEY
    )
    print("Secret added.")
except Exception as e:
    print(f"Failed to add secret: {e}")

# Prepare Dockerfile
dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt uvicorn

COPY main.py main.py

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
"""

with open("Dockerfile", "w") as f:
    f.write(dockerfile_content)

print("Uploading files...")
try:
    api.upload_file(
        path_or_fileobj="api/index.py",
        path_in_repo="main.py",
        repo_id=REPO_ID,
        repo_type="space"
    )
    
    api.upload_file(
        path_or_fileobj="api/requirements.txt",
        path_in_repo="requirements.txt",
        repo_id=REPO_ID,
        repo_type="space"
    )
    
    api.upload_file(
        path_or_fileobj="Dockerfile",
        path_in_repo="Dockerfile",
        repo_id=REPO_ID,
        repo_type="space"
    )
    print("Files uploaded successfully.")
except Exception as e:
    print(f"Failed to upload files: {e}")

print(f"Deployment to Hugging Face Spaces initiated. URL: https://{USERNAME}-{SPACE_NAME}.hf.space")
