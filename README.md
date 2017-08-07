# mailmerge
A mailmerge script written in Python.

Works with Python3.

## Usage
This script (when installed) works from the command line. Try `mailmurge -h` for help.

You can use any SMTP server you like, or pass the `--test` option to print out the messages which would be sent.

Here is an example of using gmail to send bulk mail:
```
mailmurge names.txt email.txt --hostname=smtp.gmail.com --username=your-username --sender="Your Name <your_name@gmail.com>" --tls
```
