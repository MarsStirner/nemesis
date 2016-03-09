# -*- coding: utf-8 -*-

from sqlalchemy.dialects.mysql import LONGTEXT
from nemesis.systemwide import db


class TaskInfo(db.Model):
    __bind_key__ = 'celery_tasks'
    __tablename__ = 'task_info'
    __table_args__ = (
        db.Index('start_datetime', 'start_datetime'),
        db.Index('celery_task_uuid', 'celery_task_uuid'),
        db.Index('task_name', 'task_name')
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_datetime = db.Column(db.DateTime, nullable=False)
    finish_datetime = db.Column(db.DateTime)
    task_name = db.Column(db.String(100), nullable=False)
    celery_task_uuid = db.Column(db.String(100))
    task_data = db.Column(LONGTEXT)

    def __json__(self):
        return {
            'id': self.id,
        }
