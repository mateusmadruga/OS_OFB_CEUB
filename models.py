from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy()
def now(): return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), nullable=False)
    username=db.Column(db.String(80), unique=True, nullable=False, index=True)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password_hash=db.Column(db.String(255), nullable=False); role=db.Column(db.String(40), nullable=False)
    active=db.Column(db.Boolean, default=True, nullable=False); created_at=db.Column(db.DateTime(timezone=True), default=now)
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
    @property
    def is_active(self): return self.active

class Contract(db.Model):
    id=db.Column(db.Integer,primary_key=True); number=db.Column(db.String(50),unique=True,nullable=False)
    supplier=db.Column(db.String(160),nullable=False); object=db.Column(db.Text,nullable=False)
    total_value=db.Column(db.Numeric(14,2),nullable=False,default=0); start_date=db.Column(db.Date,nullable=False); end_date=db.Column(db.Date,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class ServiceOrder(db.Model):
    id=db.Column(db.Integer,primary_key=True); number=db.Column(db.String(50),unique=True,nullable=False,index=True)
    contract_id=db.Column(db.Integer,db.ForeignKey('contract.id'),nullable=False,index=True); contract=db.relationship('Contract',backref='orders')
    kind=db.Column(db.String(10),nullable=False,default='OS'); description=db.Column(db.Text,nullable=False)
    value=db.Column(db.Numeric(14,2),nullable=False,default=0); status=db.Column(db.String(50),nullable=False,default='emitida',index=True)
    due_date=db.Column(db.Date); created_by=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)

class WorkflowEvent(db.Model):
    id=db.Column(db.Integer,primary_key=True); order_id=db.Column(db.Integer,db.ForeignKey('service_order.id'),nullable=False,index=True)
    order=db.relationship('ServiceOrder',backref=db.backref('events',lazy=True,cascade='all, delete-orphan'))
    action=db.Column(db.String(60),nullable=False); from_status=db.Column(db.String(50)); to_status=db.Column(db.String(50),nullable=False)
    notes=db.Column(db.Text); actor_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False); actor=db.relationship('User')
    created_at=db.Column(db.DateTime(timezone=True),default=now)

class AuditLog(db.Model):
    id=db.Column(db.Integer,primary_key=True); actor_id=db.Column(db.Integer,db.ForeignKey('user.id')); actor=db.relationship('User')
    action=db.Column(db.String(80),nullable=False); entity=db.Column(db.String(50),nullable=False); entity_id=db.Column(db.Integer)
    detail=db.Column(db.Text); ip=db.Column(db.String(64)); created_at=db.Column(db.DateTime(timezone=True),default=now,index=True)
