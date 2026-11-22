#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from sqlalchemy import Column, String, UnicodeText, select, func, ForeignKey
from MeowRobot.modules.sql import BASE, SESSION


# ================= TABLES ================= #

class Users(BASE):
    __tablename__ = "users"

    user_id = Column(String(14), primary_key=True)
    username = Column(UnicodeText)

    def __init__(self, user_id, username):
        self.user_id = str(user_id)
        self.username = username


class Chats(BASE):
    __tablename__ = "chats"

    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, chat_name):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name


class ChatMembers(BASE):
    __tablename__ = "chat_members"

    user_id = Column("user", String(14), ForeignKey("users.user_id"), primary_key=True)
    chat_id = Column("chat", String(14), ForeignKey("chats.chat_id"), primary_key=True)

    def __init__(self, user_id, chat_id):
        self.user_id = str(user_id)
        self.chat_id = str(chat_id)


# ================= UPDATE USER (FIXED) ================= #

def update_user(user_id, username, chat_id=None, chat_name=None):
    user_id = str(user_id)
    chat_id = str(chat_id) if chat_id else None

    try:
        # ---------- USER ----------
        user = SESSION.get(Users, user_id)
        if not user:
            SESSION.add(Users(user_id, username))
        else:
            user.username = username

        # ---------- CHAT ----------
        if chat_id and chat_name:
            chat = SESSION.get(Chats, chat_id)
            if not chat:
                SESSION.add(Chats(chat_id, chat_name))
            else:
                chat.chat_name = chat_name

            # 🔥 CRITICAL FIX (FK SAFE)
            SESSION.flush()

            # ---------- MEMBER ----------
            member = SESSION.get(ChatMembers, (user_id, chat_id))
            if not member:
                SESSION.add(ChatMembers(user_id, chat_id))

        SESSION.commit()

    except Exception as e:
        print("DB ERROR:", e)
        SESSION.rollback()


# ================= FETCH ================= #

def get_userid_by_name(username):
    return SESSION.scalars(
        select(Users).where(Users.username == username)
    ).all()


def get_name_by_userid(user_id):
    user = SESSION.get(Users, str(user_id))
    return user.username if user else None


def get_chat_name(chat_id):
    chat = SESSION.get(Chats, str(chat_id))
    return chat.chat_name if chat else None


def get_all_users():
    return SESSION.scalars(select(Users)).all()


def get_all_chats():
    return SESSION.scalars(select(Chats)).all()


def get_user_num_chats(user_id):
    return SESSION.scalar(
        select(func.count(ChatMembers.chat_id)).where(
            ChatMembers.user_id == str(user_id)
        )
    )


def get_user_com_chats(user_id):
    return SESSION.scalars(
        select(ChatMembers.chat_id).where(
            ChatMembers.user_id == str(user_id)
        )
    ).all()


def is_chat_member(chat_id, user_id):
    return SESSION.scalar(
        select(ChatMembers).where(
            ChatMembers.chat_id == str(chat_id),
            ChatMembers.user_id == str(user_id)
        )
    ) is not None


def num_users():
    return SESSION.scalar(select(func.count(Users.user_id)))


def num_chats():
    return SESSION.scalar(select(func.count(Chats.chat_id)))


# ================= MIGRATE ================= #

def migrate_chat(old_chat_id, new_chat_id):
    old_chat_id = str(old_chat_id)
    new_chat_id = str(new_chat_id)

    try:
        chat = SESSION.get(Chats, old_chat_id)

        if chat:
            SESSION.merge(Chats(new_chat_id, chat.chat_name))
            SESSION.delete(chat)

        members = SESSION.scalars(
            select(ChatMembers).where(ChatMembers.chat_id == old_chat_id)
        ).all()

        for member in members:
            SESSION.merge(ChatMembers(member.user_id, new_chat_id))
            SESSION.delete(member)

        SESSION.commit()

    except Exception as e:
        print("MIGRATE ERROR:", e)
        SESSION.rollback()
        
