"""
Allows sending mail to multiple recipients.

Each line of the names file is a name and an email address separated by commas:
name,email
John Smith,john@smith.com

The message by default is formatted with markdown unless the --html flag is
used.

The jinja2 package is used, giving you access to the following variables:
name - The name of the recipient
email - The email address of the recipient
recipient - name <email>
sender_name - The name of the sender
sender_email - The email address of the sender
sender - sender_name <sender_email>

The first line of the file is assumed to be the subject.

For example:

```
Please read this email: Offer inside:
Hi {{ name }},
Email address: {{ email }}

We're loving sending you stuff, and we have offers and such...
```

You can use tools such as cat or echo to pipe the mail message, but the names
file must be provided on the command line.
"""

import sys
from time import sleep
from getpass import getuser, getpass
from socket import getfqdn
from csv import reader
from smtplib import SMTP
from email.utils import parseaddr, formataddr
from email.message import Message
from argparse import ArgumentParser, FileType
from jinja2 import Environment
from markdown import markdown

html = """<!doctype html>
<html lang="en">
<body>
%s
</body>
</html>
"""

parser = ArgumentParser(description='Mailmerge utility')

parser.add_argument(
    'names',
    type=FileType('r'),
    help='The file to load names and email addresses from'
)

parser.add_argument(
    'message',
    nargs='?',
    type=FileType('r'),
    default=sys.stdin,
    help='The file to load the email from'
)

parser.add_argument(
    '--html',
    action='store_true',
    help='Treat the message as HTML instead of markdown'
)

parser.add_argument(
    '--sender',
    default='{0} <{0}@{1}>'.format(getuser(), getfqdn()),
    help='The email address to send mail from'
)

parser.add_argument(
    '-i',
    '--interval',
    type=float,
    default=0.25,
    help='The time to wait between SMTP connections'
)

parser.add_argument(
    '--hostname',
    default='localhost',
    help='The SMTP hostname'
)

parser.add_argument(
    '--port',
    type=int,
    default=25,
    help='The SMTP port'
)

parser.add_argument(
    '--tls',
    action='store_true',
    help='Use TLS when dealing with the SMTP server'
)

parser.add_argument(
    '--username',
    help='SMTP username'
)

parser.add_argument(
    '--password',
    help='SMTP password'
)

parser.add_argument(
    '--test',
    action='store_true',
    help='Print messages rather than sending them'
)


def main():
    args = parser.parse_args()
    if args.tls:
        print('TLS enabled.')
        if not args.username:
            args.username = input('Username: ')
        if not args.password:
            args.password = getpass('Password: ')
    kwargs = {}  # The keyword arguments for render.
    sender_name, sender_email = parseaddr(args.sender)
    kwargs['sender_name'] = sender_name
    kwargs['sender_email'] = sender_email
    # We format our own sender address in case the one on the command line is
    # malformed.
    kwargs['sender'] = formataddr((sender_name, sender_email))
    environment = Environment()
    raw_subject, raw_body = args.message.read().split('\n', 1)
    raw_subject = environment.from_string(raw_subject)
    if not args.html:
        raw_body = markdown(raw_body)
    raw_body = environment.from_string(raw_body)
    addresses = list(reader(args.names))
    total = len(addresses)
    for index, line in enumerate(addresses):
        if not line:
            continue  # Blank line.
        elif len(line) == 2:
            name, email = line
        else:
            print('Improperly formatted user: "%s".' % ','.join(line))
            continue
        kwargs['name'] = name
        kwargs['email'] = email
        recipient = formataddr((name, email))
        kwargs['recipient'] = recipient
        print('%d / %d: %s... ' % (index + 1, total, recipient), end='')
        subject = raw_subject.render(**kwargs)
        body = raw_body.render(**kwargs)
        message = Message()
        message.add_header('From', args.sender)
        message.add_header('To', recipient)
        message.add_header('Subject', subject)
        message.add_header('MIME-Version', '1.0')
        message.add_header('Content-Type', 'text/html; charset="utf-8"')
        message.set_payload(html % body)
        message = message.as_string()
        if args.test:
            print('Testing')
            print(message)
        else:
            try:
                server = SMTP(
                    host=args.hostname,
                    port=args.port
                )
                if args.tls:
                    server.starttls()
                    server.login(args.username, args.password)
                server.sendmail(sender_email, recipient, message)
                print('OK')
                sleep(args.interval)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    main()
