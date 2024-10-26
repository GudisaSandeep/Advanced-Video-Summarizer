import os
from flask import Flask
from app import app as application

if __name__ == '__main__':
    HOST = os.environ.get('HOST', '0.0.0.0')
    try:
        PORT = int(os.environ.get('PORT', '8000'))
    except ValueError:
        PORT = 8000
    application.run(HOST, PORT)
