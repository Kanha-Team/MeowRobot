#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from sqlalchemy import Column, UnicodeText, select, BigInteger

from MeowRobot.modules.sql import BASE, SESSION


class RSS(BASE):
    __tablename__ = "rss_feed"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(UnicodeText, nullable=False)
    feed_link = Column(UnicodeText)
    old_entry_link = Column(UnicodeText)

    def __init__(self, chat_id, feed_link, old_entry_link):
        self.chat_id = str(chat_id)
        self.feed_link = feed_link
        self.old_entry_link = old_entry_link

    def __repr__(self):
        return "<RSS for chatID {} at feed_link {} with old_entry_link {}>".format(
            self.chat_id, self.feed_link, self.old_entry_link
        )




def check_url_availability(tg_chat_id, tg_feed_link):
    try:
        return SESSION.scalars(
            select(RSS).where(RSS.feed_link == tg_feed_link, RSS.chat_id == str(tg_chat_id))
        ).all()
    finally:
        SESSION.close()


def add_url(tg_chat_id, tg_feed_link, tg_old_entry_link):
    with SESSION.begin():
        action = RSS(str(tg_chat_id), tg_feed_link, tg_old_entry_link)
        SESSION.add(action)


def remove_url(tg_chat_id, tg_feed_link):
    with SESSION.begin():
        # this loops to delete any possible duplicates for the same TG User ID, TG Chat ID and link
        rows = SESSION.scalars(
            select(RSS).where(RSS.feed_link == tg_feed_link, RSS.chat_id == str(tg_chat_id))
        ).all()
        for row in rows:
            SESSION.delete(row)


def get_urls(tg_chat_id):
    try:
        return SESSION.scalars(select(RSS).where(RSS.chat_id == str(tg_chat_id))).all()
    finally:
        SESSION.close()


def get_all():
    try:
        return SESSION.scalars(select(RSS)).all()
    finally:
        SESSION.close()


def update_url(row_id, new_entry_links):
    with SESSION.begin():
        row = SESSION.get(RSS, row_id)
        if row:
            # set the new old_entry_link with the latest update from the RSS Feed
            row.old_entry_link = new_entry_links[0]
