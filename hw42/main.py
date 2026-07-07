#1
import os
import shutil
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Сховище для метаданих
photos_db = []


@app.post("/photos/upload")
async def upload_photo(file: UploadFile = File(...)):
    # 1. Валідація типу
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Тільки JPEG або PNG")

    # 2. Валідація розміру (5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл завеликий (макс 5MB)")

    # 3. Збереження
    file_ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    photos_db.append({"filename": unique_name, "created_at": datetime.now()})
    return {"url": f"/photos/{unique_name}"}


@app.get("/photos/list")
async def list_photos():
    # Сортування: нові першими
    sorted_photos = sorted(photos_db, key=lambda x: x["created_at"], reverse=True)
    return [f"/photos/{p['filename']}" for p in sorted_photos]


@app.get("/photos/{filename}")
async def get_photo(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Фото не знайдено")
    return FileResponse(file_path)
#Налаштування безпеки
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#Ендпоінт для отримання токена
from fastapi import Depends


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Перевірка користувача в БД
    # 2. Перевірка пароля через pwd_context.verify(form_data.password, user.hashed_password)
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Невірні дані")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
#Захист маршрутів
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username # або об'єкт користувача з БД
    except:
        raise HTTPException(status_code=401, detail="Неавторизовано")

@app.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"user": current_user}