# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv
import pathlib

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(24).hex()
MONGO_URI = os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
WORKDIR = pathlib.Path(__file__).parent.absolute()
SERIALIZED_TOKEN = '.serialized_token.json'
