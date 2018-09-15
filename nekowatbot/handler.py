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

"""Message handlers."""

import random

import telebot

from nekowatbot import nekowat


@nekowat.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Initialize the bot."""
    response = (
        'nekowatbot - "What the!?"\n\n'
        '/add <name> : Add a new WAT\n'
        '/remove : Remove a WAT\n'
        '/wat <expression> : Get a random WAT\n'
        '/setexpressions : Set the expressions of a WAT\n'
        '/addwhitelist <name> <id> : Add user ID to whitelist\n'
        '/rmwhitelist <name> : Remove user from whitelist\n'
        '/whitelist : Show current whitelist'
    )

    nekowat.reply_to(message,response)


@nekowat.message_handler(commands=['me'])
def me(message):
    """Get user ID."""
    nekowat.reply_to(message, message.chat.id)


@nekowat.message_handler(commands=['add'])
def handle_add(message):
    """Add a new WAT to the bot.

    Expects a message with the format:

        /add <name>
    """
    chat_id = message.chat.id

    if not nekowat.is_owner(chat_id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    name = telebot.util.extract_arguments(message.text)

    if not name:
        nekowat.reply_to(message, '/add <name>')
        return

    if nekowat.wat_exists(name):
        nekowat.reply_to(message, 'There is already a WAT with that name')
        return

    msg = nekowat.send_message(
        chat_id,
        'Please send the image for this WAT'
    )

    nekowat.register_next_step_handler(
        msg,
        lambda m: process_add_image(m, name)
    )

def process_add_image(message, name):
    """Adds an image to the WAT."""
    chat_id = message.chat.id

    if message.content_type == 'text' and message.text == '/cancel':
        nekowat.send_message(chat_id, 'Operation cancelled')
        return

    if message.content_type != 'photo':
        msg = nekowat.send_message(
            chat_id,
            'Please send the image for this WAT'
        )

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_add_image(m, name)
        )

        return

    # Get file IDs
    file_ids = [p.file_id for p in message.photo]

    # Create record
    nekowat.create_wat(name, file_ids)

    nekowat.send_message(chat_id, 'Added correctly!')


@nekowat.message_handler(commands=['remove'])
def handle_remove(message):
    """Handle removing a WAT.

    This shows all wats by name.
    """
    chat_id = message.chat.id

    if not nekowat.is_owner(chat_id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)

    for w in nekowat.get_all_wats():
        markup.add(telebot.types.KeyboardButton(w['name']))

    # Add cancel
    markup.add(telebot.types.KeyboardButton('/cancel'))

    msg = nekowat.send_message(
        chat_id,
        'Choose a WAT to delete',
        reply_markup=markup
    )

    nekowat.register_next_step_handler(
        msg,
        lambda m: process_remove_wat(m)
    )

def process_remove_wat(message):
    """Removes a WAT from database."""
    chat_id = message.chat.id
    hide_markup = telebot.types.ReplyKeyboardRemove(selective=False)

    if message.content_type != 'text':
        msg = nekowat.send_message(chat_id, 'You need to send a bot name')

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_remove_wat(m)
        )

        return

    if message.text == '/cancel':
        nekowat.send_message(
            chat_id,
            'Operation cancelled',
            reply_markup=hide_markup
        )

        return

    # Fetch wat
    name = message.text
    wat = nekowat.get_wat(name)

    if not wat:
        msg = nekowat.send_message(chat_id, 'No WAT found with that name')

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_remove_wat(m)
        )

        return

    # Remove
    result = nekowat.remove_wat(wat.doc_id)

    if result:
        nekowat.send_message(
            chat_id,
            'Removed WAT %s' % name,
            reply_markup=hide_markup
        )
        return

    nekowat.send_message(
        chat_id,
        'Failed to remove WAT WAT %s' % name,
        reply_markup=hide_markup
    )
    return


@nekowat.message_handler(commands=['wat'])
def handle_wat(message):
    """Get a random WAT based on the received expression.

    Expects a message with the format:

        /wat <expression>

    If the expression is empty, gets a random WAT.
    """
    if not nekowat.is_allowed(message.from_user.id):
        return

    # Normalize expression
    expression = telebot.util.extract_arguments(message.text).lower()

    if not expression:
        # Get all images
        wats = nekowat.get_all_wats()

    else:
        # Get by expression
        wats = nekowat.get_wats_by_expression(expression)

        if not wats:
            # Default to all WATs
            wats = nekowat.get_all_wats()

    if not wats:
        # Happens when database is empty
        nekowat.reply_to(
            message,
            'Sorry, I have no WATs that match that'
        )
        return

    # Choose random WAT and send file
    wat = random.choice(wats)

    nekowat.send_photo(
        message.chat.id,
        wat['file_ids'][-1], # Get biggest image
        reply_to_message_id=message.message_id
    )


@nekowat.message_handler(commands=['setexpressions'])
def handle_set_expressions(message):
    """Sets expressions for a WAT.

    This shows all wats by name and then displays the expressions of the
    WAT that was chosen.
    """
    chat_id = message.chat.id

    if not nekowat.is_owner(chat_id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)

    for w in nekowat.get_all_wats():
        markup.add(telebot.types.KeyboardButton(w['name']))

    # Add cancel
    markup.add(telebot.types.KeyboardButton('/cancel'))

    msg = nekowat.send_message(
        chat_id,
        'Choose a WAT to modify',
        reply_markup=markup
    )

    nekowat.register_next_step_handler(
        msg,
        lambda m: process_get_expressions(m)
    )

def process_get_expressions(message):
    """Shows the expressions of the selected WAT and asks for new ones."""
    chat_id = message.chat.id
    hide_markup = telebot.types.ReplyKeyboardRemove(selective=False)

    if message.content_type != 'text':
        msg = nekowat.send_message(chat_id, 'You need to send a WAT name')

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_get_expressions(m)
        )

        return

    if message.text == '/cancel':
        nekowat.send_message(
            chat_id,
            'Operation cancelled',
            reply_markup=hide_markup
        )

        return

    # Fetch wat
    name = message.text
    wat = nekowat.get_wat(name)

    if not wat:
        msg = nekowat.send_message(chat_id, 'No WAT found with that name')

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_get_expressions(m)
        )

        return

    # Show expressions
    expressions = ','.join(wat['expressions'])

    msg = nekowat.send_message(
        chat_id,
        'Expressions of %s' % name,
        reply_markup=hide_markup
    )

    nekowat.reply_to(msg, expressions or '[No expressions defined]')

    msg = nekowat.send_message(
        chat_id,
        'Send a comma separated list of expressions'
    )

    nekowat.register_next_step_handler(
        msg,
        lambda m: process_set_expressions(m, name)
    )

def process_set_expressions(message, name):
    """Sets the expressions a wat."""
    chat_id = message.chat.id

    if message.content_type != 'text':
        msg = nekowat.send_message(
            chat_id,
            'You need to send a comma separated list of expressions'
        )

        nekowat.register_next_step_handler(
            msg,
            lambda m: process_set_expressions(m, name)
        )

        return

    if message.text == '/cancel':
        nekowat.send_message(
            chat_id,
            'Operation cancelled'
        )

        return

    # Update record
    expressions = [e.lower().strip() for e in message.text.split(',')]
    nekowat.set_wat_expressions(name, expressions)

    nekowat.send_message(chat_id, 'Expressions updated')


@nekowat.message_handler(commands=['addwhitelist'])
def handle_add_whitelist(message):
    """Add a user to the whitelist.

    Expects a message with the format:

        /addwhitelist <name> <id>
    """
    if not nekowat.is_owner(message.chat.id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    args = telebot.util.extract_arguments(message.text).split(' ')

    if len(args) != 2:
        nekowat.reply_to(message, '/addwhitelist <name> <id>')
        return

    try:
        name = args[0]
        user_id = int(args[1])

    except:
        nekowat.reply_to(message, '/addwhitelist <name> <id>')
        return

    if nekowat.add_whitelist(name, user_id):
        nekowat.reply_to(message, 'User added to whitelist!')
        return

    nekowat.reply_to(message, 'Failed to add user to whitelist')


@nekowat.message_handler(commands=['rmwhitelist'])
def handle_rm_whitelist(message):
    """Remove a user from the whitelist.

    Expects a message with the format:

        /rm-whitelist <name>
    """
    if not nekowat.is_owner(message.chat.id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    name = telebot.util.extract_arguments(message.text)

    if nekowat.rm_whitelist(name):
        nekowat.reply_to(message, 'User removed from whitelist!')
        return

    nekowat.reply_to(message, 'Failed to remove user from whitelist')


@nekowat.message_handler(commands=['whitelist'])
def handle_show_whitelist(message):
    """Show current whitelist."""
    if not nekowat.is_owner(message.chat.id):
        nekowat.reply_to(message, 'You do not have permission to do that')
        return

    msg = 'Whitelisted users:\n\n'
    for name, uid in nekowat.whitelist.items():
        msg += '- %s (%d)\n' % (name, uid)

    nekowat.reply_to(message, msg)


@nekowat.inline_handler(lambda query: True)
def handle_inline(inline_query):
    """Answers inline queries.

    If no text is specified, returns a list of all WATs available. If text is
    specified, this is used as an expression to search for WATs in the
    database.
    """
    if not nekowat.is_allowed(inline_query.from_user.id):
        return

    # Normalize expression
    expression = inline_query.query.lower().strip()

    if not expression:
        # Get all images
        wats = nekowat.get_all_wats()

    else:
        # Get by expression
        wats = nekowat.get_wats_by_expression(expression)

    try:
        responses = []

        for index, wat in enumerate(wats):
            r = telebot.types.InlineQueryResultCachedPhoto(
                str(index),
                # Get smallest file for inline reply
                wat['file_ids'][0],
                parse_mode='' # Workaround for Telegram API error
            )

            responses.append(r)

        nekowat.answer_inline_query(inline_query.id, responses)

    except Exception as e:
        print(e)
