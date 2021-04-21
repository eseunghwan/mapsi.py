# -*- coding: utf-8 -*-
from browser import document, webcomponent, html
from browser.template import Template


## routers
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
        if Mapsi.router == None:
            raise RuntimeError("router-link can be used router-view exists!")

        document.select("router-view")[0].show_route(self.__name)

class RouterView:
    def show_route(self, name:str):
        self.innerHTML = ""

        for route in Mapsi.router:
            if route["url"] == name:
                self.innerHTML += f"<{route['el']} />"
            else:
                self.innerHTML += f"<!-- <{route['el']} /> -->"

    def render(self):
        self.innerHTML = ""
        for idx, route in enumerate(Mapsi.router):
            if idx == 0:
                self.innerHTML += f"<{route['name'].lower()}-app />"
            else:
                self.innerHTML += f"<!-- <{route['name'].lower()}-app /> -->"

class Router:
    def __init__(self, routes:list = []):
        self.routes = routes

webcomponent.define("router-link", RouterLink)
webcomponent.define("router-view", RouterView)


## DOM/Component
event_attrs = [ "click", "doubleClick", "change", "input" ]
value_attrs = [ "model" ]
value_attrs_to_change = {
    "model": "value"
}

EventStore:dict = {}
DataStore:dict = {}

class Eventer:
    def __init__(self, comp, event_name:str):
        self.__comp = comp
        self.__method = comp.methods[event_name]

    def call(self, event):
        self.__method(self.__comp, event)
        self.__comp.render_dom(
            self.__comp.firstChild,
            self.__comp.__class__.parameter(),
            self.__comp.__class__.data(),
            self.__comp.methods,
            False
        )

class VDOM:
    def __init__(self):
        self.dom_templates = {}

    def set_dom_templates(self, root):
        if not root == self.firstChild and root.childElementCount == 0:
            self.dom_templates[root] = root.innerText

        for child in root.childNodes:
            if not hasattr(child, "tagName"):
                continue

            self.set_dom_templates(child)

    def render_dom(self, dom, params, data, methods, bind_events:bool = True):
        format_info = {}
        if hasattr(params, "__iter__"):
            for key in params:
                format_info[key] = str(self.getAttribute(key))
                self.removeAttribute(key)
        
        if hasattr(data, "__iter__"):
            for key in data:
                format_info[key] = str(getattr(self, key))

        for child in dom.childNodes:
            if not hasattr(child, "tagName"):
                continue

            for key in child.attrs:
                value = child.attrs[key]

                if key.startswith(":"):
                    dom_key = key[1:]
                    if bind_events and dom_key in event_attrs:
                        child.bind(dom_key, Eventer(self, value).call)
                    elif dom_key in value_attrs:
                        child.setAttribute(value_attrs_to_change[dom_key], value.format(**format_info))

                    child.removeAttribute(key)

            if child.childElementCount == 0:
                child.innerText = self.dom_templates[child].format(**format_info)

            self.render_dom(child, data, methods, bind_events)

    # methods on registration
    def created(self):
        pass

    def mounted(self):
        pass

class Component(VDOM):
    template:str = ""
    el:str = ""

    def __init__(self):
        super().__init__()

        self.clear()
        # self.setAttribute("class", "mapsi-comp")

        self.innerHTML = self.replace_comp_tags()
        if "id" in self.firstChild.attrs:
            self.firstChild.removeAttribute("id")

        self.__dom_texts = {}
        self.set_dom_templates(self.firstChild)

        for name in self.__class__.parameter():
            setattr(self.__class__, name, self.__class__.parameter()[name])

        for name in self.__class__.data():
            setattr(self.__class__, name, self.__class__.data()[name])

        self.created()
        self.mounted()
        self.render()

    def replace_comp_tags(self) -> str:
        template = self.template.strip()
        for comp in Mapsi.components:
            if not comp in ("#comp-main-app", self.el):
                comp_tag = comp[6:-4].lower()
                dom_comp_tag = comp[6:]

                template = template.replace(
                    f"<{comp_tag} ", f"<{dom_comp_tag} "
                ).replace(
                    f"</{comp_tag}>", f"</{dom_comp_tag}>"
                )

        return template

    def render(self):
        params, data = self.__class__.parameter(), self.__class__.data()
        self.render_dom(self.firstChild, params, data, self.methods)

    @staticmethod
    def data() -> dict:
        return {}

    @staticmethod
    def parameter() -> dict:
        return {}

    @property
    def methods(self) -> dict:
        if self.el in EventStore:
            return EventStore[self.el]
        else:
            return {}

    @staticmethod
    def method(fn):
        def decorator(fn):
            comp_name = "#comp-" + str(fn).split(".")[0][10:].lower() + "-app"
            if not comp_name in EventStore:
                EventStore[comp_name] = {}

            EventStore[comp_name][fn.__name__] = fn
            return fn

        return decorator(fn)


## Mapsi
MapsiCompStyle = html.STYLE()
MapsiCompStyle.clear()
MapsiCompStyle.setAttribute("class", "mapsi-comp")
document.head <= MapsiCompStyle

class Mapsi:
    components:list = []
    router:list = []

    @staticmethod
    def use(obj):
        if isinstance(obj, Router):
            Mapsi.router = obj.routes

    @staticmethod
    def render(main_app:Component):
        Mapsi.register_component("main-app", main_app)

    @staticmethod
    def register(name:str):
        def decorator(comp:Component):
            Mapsi.register_component(name, comp)
            return comp

        return decorator

    @staticmethod
    def register_component(name:str, comp:Component):
        comp_name = f"#comp-{name}"
        setattr(comp, "el", comp_name)

        MapsiCompStyle.innerText += name + "{display: block;}"
        # print(123456789, document.select("style")[0].innerText)

        if not comp_name in Mapsi.components:
            Mapsi.components.append(comp_name)

        webcomponent.define(name, comp)

        if not comp.__name__ == "App":
            for idx, route in enumerate(Mapsi.router):
                if route["name"].lower() == comp.__name__.lower():
                    Mapsi.router[idx]["el"] = name
