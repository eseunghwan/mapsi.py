# -*- coding: utf-8 -*-
from browser import document, html
from mapsi import Mapsi

def setup():
    import app_main

    real_app_elm = html.maketag("main-app")()
    document.body.removeChild(document.select("App")[0])
    document.body <= real_app_elm

    app_main.setup()

    import views
    import components

    from App import App as main_app
    Mapsi.render(main_app)

    may_router_view = document.select("router-view")
    if len(may_router_view) > 0:
        may_router_view[0].render()
