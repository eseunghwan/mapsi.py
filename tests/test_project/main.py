# -*- coding: utf-8 -*-
from mapsi import Mapsi, Router
from router import routes

def setup():
    Mapsi.use(Router(routes))
