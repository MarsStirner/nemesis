# -*- coding: utf-8 -*-
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class UserMail(db.Model):
    __tablename__ = "UserMail"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.ForeignKey('Person.id'), nullable=True)
    recipient_id = db.Column(db.ForeignKey('Person.id'), nullable=True)
    subject = db.Column(db.String(256), nullable=False)
    text = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    read = db.Column(db.Integer, nullable=False)
    mark = db.Column(db.Integer)
    parent_id = db.Column(db.ForeignKey('UserMail.id'), nullable=True)
    folder = db.Column(db.String(50), nullable=False)

    sender = db.relationship('Person', foreign_keys=[sender_id])
    recipient = db.relationship('Person', foreign_keys=[recipient_id])

    def __json__(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'text': self.text,
            'datetime': self.datetime,
            'read': bool(self.read),
            'mark': bool(self.mark),
            'parent_id': self.parent_id,
            'folder': self.folder
        }


class UserSubscriptions(db.Model):
    __tablename__ = "UserSubscriptions"
    __table_args__ = (db.Index(u'object_id', u'person_id'), )

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(256), index=True)
    person_id = db.Column(db.ForeignKey("Person.id"))

    person = db.relationship('Person', backref='_subscriptions')

    @classmethod
    def list_subscriptions(cls, person):
        return (result.object_id for result in cls.query.filter(cls.person_id == int(person)))

    @classmethod
    def list_subscribers(cls, object_id):
        return (result.person_id for result in cls.query.filter(cls.object_id == object_id))

