from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.models import user
from fastapi import Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.models.user import User
from app.models.task import Task
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth import get_current_user


app = FastAPI()
Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, hashed_password=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password): # type: ignore
        raise HTTPException(status_code=400, detail="Invalid email or password")

    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_task = Task(
        title=task.title,
        description=task.description,
        user_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).order_by(Task.id.desc()).all()
    return tasks

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_task_or_404(task_id, db, int(current_user.id))

    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.done is not None:
        task.done = task_update.done

    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_task_or_404(task_id, db, int(current_user.id))
    db.delete(task)
    db.commit()
    return None

def get_task_or_404(task_id: int, db: Session, user_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task