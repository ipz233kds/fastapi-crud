from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import models, schemas, crud, auth
from database import SessionLocal, engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)  # Ініціалізація БД

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(db, token)

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Неавторизований користувач")
    return current_user

def get_admin_user(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостатньо прав")
    return current_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth.authenticate_user(db, form_data.username, form_data.password)

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=list[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_admin_user)):
    user = crud.delete_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return {"message": "Користувач видалений"}