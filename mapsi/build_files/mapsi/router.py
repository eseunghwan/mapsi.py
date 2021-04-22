# -*- coding: utf-8 -*-
from browser import document, webcomponent, html


RouteStore:list = None

class RouterLink:
    def __init__(self):
        self.__name = self.getAttribute("to")
        self.removeAttribute("to")

        inner = self.innerHTML
        self.clear()

        container = html.DIV()
        container.innerHTML = inner
        container.bind("click", self.show_route)
        
        self.appendChild(container)

    def show_route(self, event):
        if RouteStore == None:
            raise RuntimeError("router-link can be used router-view exists!")

        document.select("router-view")[0].show_route(self.__name)

class RouterView:
    def show_route(self, name:str):
        self.innerHTML = ""

        for route in RouteStore:
            if route["url"] == name:
                self.innerHTML += f"<{route['el']} />"
            else:
                self.innerHTML += f"<!-- <{route['el']} /> -->"

    def render(self):
        self.innerHTML = ""
        for idx, route in enumerate(RouteStore):
            if idx == 0:
                self.innerHTML += f"<{route['name'].lower()}-app />"
            else:
                self.innerHTML += f"<!-- <{route['name'].lower()}-app /> -->"

class Router:
    def __init__(self, routes:list = []):
        global RouteStore
        RouteStore = routes

webcomponent.define("router-link", RouterLink)
webcomponent.define("router-view", RouterView)
