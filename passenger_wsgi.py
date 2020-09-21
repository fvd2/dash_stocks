import imp
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from stock_prices import app

application = app.server
