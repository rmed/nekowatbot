# -*- coding: utf-8 -*-
#
# nekowatbot
# https://github.com/rmed/nekowatbot
#
# The MIT License (MIT)
#
# Copyright (c) 2018 Rafael Medina García <rafamedgar@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Bot implementation."""

import logging
import json
import os
import sys

import telebot

from tinydb import TinyDB, Query
from tinydb_smartcache import SmartCacheTable


class Nekowat(object):
    """Attributes:

    _conf_path (str): Path to the configuration file.
    _conf (dict): Parsed configuration
    token (str): Telegram bot token
    owner (int): ID of the bot owner. The owner can do certain special actions
        such as adding or removing users from whitelist.
    use_whitelist (bool): Flag indicating whether the bot allows commands from
        any user (False) or only users defined in the whitelist (True)
    whitelist (dict): Users that are allowed to interact with the bot.
        It uses the following structure:

            {
                'user1': 123456789,
                'user2': 123456788
            }

    bot (TeleBot): TeleBot instance.
    db (TinyDB): Database instance.
    wat (Query): TinyDB query.
    """

    def init_bot(self, config_path=None, level='INFO'):
        """Initializer.

        Args:
            config_path (str): Path to the configuration file. If this is not
                provided, the bot expects the path to be available in the
                environment variable 'NEKOWAT_CONF'.
            level (str): Logging level to use in the internal logger of the bot.
        """
        # Parse configuration file
        if not config_path:
            config_path = os.path.abspath(os.getenv('NEKOWAT_CONF', ''))

        if not config_path or not os.path.isfile(config_path):
            sys.exit('Could not find configuration file')

        self._conf_path = config_path

        with open(config_path) as f:
            self._conf = json.load(f)

        # Bot settings
        self.token = self._conf['tg']['token']
        self.owner = self._conf['tg']['owner']
        self.use_whitelist = self._conf['tg']['use_whitelist']
        self.whitelist = self._conf['tg']['whitelist']

        # TinyDB
        #
        # Row structure:
        #
        # - name (str): Name of the file
        # - file_ids (list): List of file IDs ordered by size
        # - expressions (list): List of expressions that match the image
        self.db = TinyDB(self._conf['db'])
        self.db.table_class = SmartCacheTable
        self.wat = Query()

        # Bot initialization
        telebot.logger.setLevel(level)
        self.bot = telebot.TeleBot(
            self.token,
            threaded=True,
            skip_pending=True
        )

        # Inherit bot methods
        self.answer_inline_query = self.bot.answer_inline_query
        self.inline_handler = self.bot.inline_handler
        self.message_handler = self.bot.message_handler
        self.register_next_step_handler = self.bot.register_next_step_handler
        self.reply_to = self.bot.reply_to
        self.send_message = self.bot.send_message
        self.send_photo = self.bot.send_photo

    def start(self):
        """Bot starter."""
        print('Start polling')
        self.bot.polling(none_stop=True)

    def stop(self):
        """Bot stopper."""
        print('Stop polling')
        self.bot.stop_polling()

    def is_owner(self, user_id):
        """Checks whether a message comes from the owner."""
        return user_id == self.owner

    def is_allowed(self, user_id):
        """Checks whether a message comes from a whitelisted user.

        Note that disabling the whitelist results in every user being able
        to communicate with the bot.
        """
        if not self.use_whitelist or user_id == self.owner:
            return True

        return user_id in self.whitelist.values()

    def add_whitelist(self, name, user_id):
        """Adds a user to the whitelist.

        This updates the configuration file.

        Args:
            name (str): Name of the user.
            user_id (int): User ID.

        Returns:
            Boolean indicating if the user was added or not.
        """
        if name in self.whitelist.keys():
            # Already exists
            return False

        self.whitelist[name] = user_id
        self._conf['tg']['whitelist'] = self.whitelist

        with open(self._conf_path, 'w') as f:
            json.dump(self._conf, f)

        return True

    def rm_whitelist(self, name):
        """Removes a user from the whitelist.

        This updates the configuration file.

        Args:
            name (str): Name of the user.

        Returns:
            Boolean indicating if the user was removed or not.
        """
        if name not in self.whitelist.keys():
            # Does not exist
            return False

        del self.whitelist[name]
        self._conf['tg']['whitelist'] = self.whitelist

        with open(self._conf_path, 'w') as f:
            json.dump(self._conf, f)

        return True

    def create_wat(self, name, file_ids):
        """Insert a new wat record in the database.

        Args:
            name (str): Name of the wat.
            file_ids (list[str]): List of file IDs in Telegram (ordered by size)
        """
        self.db.insert({
            'name': name,
            'file_ids': file_ids,
            'expressions': []
        })

    def get_all_wats(self):
        """Get all wats from the database.

        Returns:
            List of tuples containing file ID and name
        """
        return self.db.all()

    def get_wats_by_expression(self, expression):
        """Get all rows that match an expression.

        Returns:
            List of database rows
        """
        return self.db.search(self.wat.expressions.any([expression]))

    def wat_exists(self, name):
        """Check whether a wat exists already."""
        wat = self.db.get(self.wat.name == name)

        if wat:
            return True

        return False

    def get_wat(self, name):
        """Get a WAT by name."""
        return self.db.get(self.wat.name == name)

    def set_wat_expressions(self, name, expressions):
        """Update a WAT and set the new expressions."""
        self.db.update(
            {'expressions': expressions},
            self.wat.name == name
        )

    def remove_wat(self, doc_id):
        """Remove a WAT by ID."""
        return self.db.remove(doc_ids=[doc_id,])


# Bot instance
nekowat = Nekowat()
