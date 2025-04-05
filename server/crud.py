from sqlalchemy.orm import Session
from models import Expense, User
from schemas import *
from typing import List, Optional
from datetime import date

def create_expense(db: Session, expense: ExpenseCreate):
    user = db.query(User).filter(User.telegram_id == expense.telegram_id).first()
    if not user:
        return None  
    
    db_expense = Expense(
        name=expense.name,
        date=expense.date,
        amount_uah=expense.amount_uah,
        amount_usd=expense.amount_usd,
        user_id=user.id 
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def get_expenses(db: Session, telegram_id: int, start_date: Optional[date] = None,
    end_date: Optional[date] = None, expense_id: Optional[int] = None):
    
    query = db.query(Expense).join(User).filter(User.telegram_id == telegram_id)
    
    if start_date and end_date:
        query = query.filter(Expense.date.between(start_date, end_date))
    
    if expense_id:
        query = query.filter(Expense.id == expense_id)
    
    query = query.order_by(Expense.date)
    
    return query.all()


def update_expense(db: Session, expense_id: int, expense: ExpenseCreate):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return None
    
    db_expense.name = expense.name
    db_expense.date = expense.date
    db_expense.amount_uah = expense.amount_uah
    db_expense.amount_usd = expense.amount_usd
    db.commit()
    db.refresh(db_expense)
    
    return db_expense

def delete_expense(db: Session, expense_id: int):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return None
    
    db.delete(db_expense)
    db.commit()
    
    return db_expense


def create_user(db: Session, user_data: UserCreate):
    existing_user = db.query(User).filter(User.telegram_id == user_data.telegram_id).first()
    if existing_user:
        return existing_user
    
    new_user = User(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()