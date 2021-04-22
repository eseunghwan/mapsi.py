# -*- coding: utf-8 -*-
from browser import document, html, webcomponent
from .router import Router
from .vdom import VirtualDOM, VirtualEventer

EventStore:dict = {}

MapsiCompStyle = html.STYLE()
MapsiCompStyle.clear()
MapsiCompStyle.setAttribute("class", "mapsi-comp")
document.head <= MapsiCompStyle

class Component:
    template:str = ""
    el:str = ""

    def __init__(self):
        template_replaced = self.template.strip()
        for comp in Mapsi.components:
            if not comp in ("comp-main-app", self.el):
                comp_tag = comp[5:-4].lower()
                dom_comp_tag = comp[5:]

                template_replaced = template_replaced.replace(
                    f"<{comp_tag} ", f"<{dom_comp_tag} "
                ).replace(
                    f"</{comp_tag}>", f"</{dom_comp_tag}>"
                )

        for p_name in self.__class__.parameter():
            setattr(self, p_name, str(self.getAttribute(p_name)))
            self.removeAttribute(p_name)

        for d_name in self.__class__.data():
            setattr(self, d_name, self.__class__.data()[d_name])

        self.created()

        self.innerHTML = template_replaced
        self.mounted()

        self.__vdom = VirtualDOM(self, self.firstChild)
        self.render()

    def created(self):
        pass

    def mounted(self):
        pass

    def render(self):
        self.__vdom.render()

    @staticmethod
    def data() -> dict:
        return {}

    @property
    def current_datas(self) -> dict:
        return {
            d_name: getattr(self, d_name)
            for d_name in self.__class__.data()
        }

    @staticmethod
    def parameter() -> dict:
        return {}

    @property
    def current_parameters(self) -> dict:
        return {
            p_name: getattr(self, p_name)
            for p_name in self.__class__.parameter()
        }

    @property
    def methods(self) -> dict:
        if self.el in EventStore:
            return {
                e_name: VirtualEventer(self, e_name)
                for e_name in EventStore[self.el]
            }
        else:
            return {}

    @staticmethod
    def method(fn):
        def decorator(fn):
            comp_name = "comp-" + str(fn).split(".")[0][10:].lower() + "-app"
            if not comp_name in EventStore:
                EventStore[comp_name] = {}

            EventStore[comp_name][fn.__name__] = fn
            return fn

        return decorator(fn)


class Mapsi:
    components:list = []
    routes:list = []

    @staticmethod
    def use(obj):
        if isinstance(obj, Router):
            from .router import RouteStore
            Mapsi.routes = RouteStore

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
        comp_name = f"comp-{name}"
        setattr(comp, "el", comp_name)

        comp_style = {"display": "block"}
        # if name == "main-app":
        #     comp_style["display"] = "block"

        comp_style_to_add = ";".join([f"{key}:{value}" for key, value in comp_style.items()])
        if not comp_style_to_add == "":
            MapsiCompStyle.innerText += name + "{" + comp_style_to_add + ";}"

        if not comp_name in Mapsi.components:
            Mapsi.components.append(comp_name)

        webcomponent.define(name, comp)

        if not comp.__name__ == "App":
            for idx, route in enumerate(Mapsi.routes):
                if route["name"].lower() == comp.__name__.lower():
                    Mapsi.routes[idx]["el"] = name
