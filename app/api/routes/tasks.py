import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.errors import task_not_found_error
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

def get_task_or_404(task_id: int, db: Session, user_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task is None:
        logger.warning("Task not found: task_id=%s user_id=%s", task_id, user_id)
        raise task_not_found_error()
    return task

@router.post(
    "",
    response_model=TaskResponse,
    responses={
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "http_401", "message": "Not authenticated"},
                        "detail": "Not authenticated",
                    }
                }
            },
        }
    },
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Task:
    db_task = Task(
        title=task.title,
        description=task.description,
        user_id=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    logger.info("Task created: user_id=%s title=%s", current_user.id, task.title)
    return db_task

@router.get(
    "",
    response_model=TaskListResponse,
    responses={
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "http_401", "message": "Not authenticated"},
                        "detail": "Not authenticated",
                    }
                }
            },
        },
        422: {
            "description": "Validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "validation_error",
                            "message": "Validation failed",
                            "details": [
                                {
                                    "loc": ["query", "limit"],
                                    "msg": "Input should be less than or equal to 100",
                                    "type": "less_than_equal",
                                }
                            ],
                        },
                        "detail": "Validation failed",
                    }
                }
            },
        },
    },
)
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    done: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if done is not None:
        query = query.filter(Task.done == done)

    total = query.count()

    items = (
        query.order_by(Task.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info("Retrieved tasks for user_id: %s", current_user.id)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    responses={
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "http_401", "message": "Not authenticated"},
                        "detail": "Not authenticated",
                    }
                }
            },
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "task_not_found", "message": "Task not found"},
                        "detail": "Task not found",
                    }
                }
            },
        },
    },
)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Task:
    task = get_task_or_404(task_id, db, int(current_user.id))

    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.done is not None:
        task.done = task_update.done

    db.commit()
    db.refresh(task)
    logger.info("Task updated: task_id=%s user_id=%s", task.id, current_user.id)
    return task

@router.delete(
    "/{task_id}",
    status_code=204,
    responses={
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "http_401", "message": "Not authenticated"},
                        "detail": "Not authenticated",
                    }
                }
            },
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "task_not_found", "message": "Task not found"},
                        "detail": "Task not found",
                    }
                }
            },
        },
    },
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    task = get_task_or_404(task_id, db, int(current_user.id))
    db.delete(task)
    db.commit()
    logger.info("Task deleted: task_id=%s user_id=%s", task.id, current_user.id)
    return None
