from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, crud
from schemas import *
from database import get_db, engine, SessionLocal
from typing import List, Optional

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.post("/expenses/", response_model=ExpenseResponse)
def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, expense)

@app.get("/expenses/", response_model=List[ExpenseResponse])
def get_expenses(telegram_id: int, start_date: Optional[date] = None,
    end_date: Optional[date] = None, expense_id: Optional[int] = None,
    db: Session = Depends(get_db)
    ):
    
    expenses = crud.get_expenses(db=db, telegram_id=telegram_id, start_date=start_date, end_date=end_date, expense_id=expense_id)
    
    if not expenses:
        raise HTTPException(status_code=404, detail="No expenses found")
    
    return expenses

@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    updated_expense = crud.update_expense(db=db, expense_id=expense_id, expense=expense)
    
    if not updated_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return updated_expense

@app.delete("/expenses/{expense_id}", response_model=ExpenseResponse)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    deleted_expense = crud.delete_expense(db=db, expense_id=expense_id)
    
    if not deleted_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return deleted_expense

@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users/{telegram_id}", response_model=UserResponse)
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_telegram_id(db=db, telegram_id=telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

def convert_to_date(date_str: str) -> Optional[datetime.date]:
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use dd.mm.YYYY. Provided: {date_str}")