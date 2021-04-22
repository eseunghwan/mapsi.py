# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass
from typing import List
from lxml.html import fromstring, tostring
from copy import deepcopy

@dataclass
class Component:
    el: str
    dom_el:str
    template:str
    style:str
    python:str

    def render(self, include_prefix:bool = True) -> str:
        if self.template.strip() == "":
            return ""

        if include_prefix:
            real_python = "# -*- coding: utf-8 -*-\nfrom mapsi import Mapsi, Component, DataStore\n\n" + self.python
        else:
            real_python = "\n" + self.python

        if "scoped" in self.style.split("\n")[0]:
            style_split = self.style.replace(self.style.split("\n")[0], "<style>").split("\n")
            style_scoped = []
            for line in style_split:
                if line.strip().endswith("{"):
                    if line.strip().startswith(self.dom_el):
                        style_scoped.append(line.replace(self.dom_el, f"{self.dom_el}>div"))
                    elif line.strip().startswith(self.el):
                        style_scoped.append(line.replace(self.el, f"{self.dom_el}>div"))
                    else:
                        style_scoped.append(line.replace(line.strip(), f"{self.dom_el}>div>{line.strip()}"))
                else:
                    style_scoped.append(line)

            real_style = "\n".join(style_scoped)
        else:
            real_style = self.style.replace(self.el, self.dom_el)

        class_line = f"class {self.el}(Component):"
        return real_python.replace(
            class_line,
            class_line + f'''
    template = """
{self.template}
    {real_style}"""
'''
        )

    def render_to_file(self, dest:str, mode:str = "w"):
        with open(dest, mode, encoding = "utf-8") as rtf:
            rtf.write(self.render(mode == "w"))


value_attrs = [ "model" ]
cond_attrs = [ "if", "elif", "else" ]
ConditionStore = { "if": "", "elif": [] }
loop_attrs = [ "for" ]
class Parser:
    @staticmethod
    def load_mapsi(mapsi_file:str) -> Component:
        with open(mapsi_file, "r", encoding = "utf-8") as mr:
            blocks = Parser.get_blocks(mr.read(), os.path.splitext(os.path.basename(mapsi_file))[0])

        return Component(**blocks)

    @staticmethod
    def load_mapsi_from_directory(root:str) -> List[Component]:
        from glob import glob

        return [
            Parser.load_mapsi(mapsi_file)
            for mapsi_file in glob(os.path.join(root, "*.mapsi"))
        ]

    @staticmethod
    def get_blocks(source:str, name:str) -> dict:
        blocks = { "template": "", "style": "", "el": name }
        if name.lower() == "app":
            blocks["dom_el"] = "main-app"
        else:
            blocks["dom_el"] = f"{name.lower()}-app"

        if "<template>" in source and "</template>" in source:
            blocks["template"] = source.split("<template>\n")[1].split("\n</template>")[0]
            blocks["template"] = Parser.render_template_as_dom(blocks["template"])

        if "<style" in source and "</style>" in source:
            style = source.split("<style")[1].split("\n</style>")[0]
            blocks["style"] = "<style" + style + "\n</style>"

        if "<python>" in source and "</python>" in source:
            python = source.split("<python>\n")[1].split("\n</python>")[0]
            blocks["python"] = "\n".join([
                line
                for line in python.split("\n")
                if not "pass" in line
            ])

            class_line = blocks["python"].split("\n")[0]
            class_line_to_change = f"""
class {name}(Component):
    def __init__(self):
        super().__init__()
"""

            if not name.lower() == "app":
                class_line_to_change = f'@Mapsi.register("{name.lower()}-app")' + class_line_to_change
            
            blocks["python"] = blocks["python"].replace(
                class_line, class_line_to_change
            # ).replace(
            #     "Component.", f"{name}."
            # ).replace(
            #     "self.", f"{name}."
            # ).replace(
            #     f"@{name}.", "@Component."
            ) + "\n"
        else:
            blocks["python"] = f"""
class {name}(Component):
    def __init__(self):
        super().__init__()
"""

            if not name.lower() == "app":
                blocks["python"] = f'@Mapsi.register("{name.lower()}-app")' + blocks["python"]

        return blocks

    @staticmethod
    def render_template_as_dom(template:str) -> str:
        if template == "":
            return template

        for key in ConditionStore.keys():
            ConditionStore[key] = None

        dom = fromstring(template)
        dom = Parser.change_dom_for_template(dom)
        return tostring(dom).decode("utf-8").replace(
            "&lt;", "<"
        ).replace(
            "&gt;", ">"
        )

    @staticmethod
    def change_dom_for_template(dom):
        if not dom.text in ("", None):
            if "{" in dom.text and "}" in dom.text:
                dom.text = dom.text.replace("{ ", "{").replace(" }", "}")

        attribs = deepcopy(dom.attrib)

        for key, value in attribs.items():
            if key.startswith(":"):
                r_key = key[1:]
                if r_key in value_attrs:
                    if not value.startswith("{"):
                        value = "{" + value
                    
                    if not value.startswith("}"):
                        value = value + "}"

                    dom.attrib[key] = value
                elif r_key in cond_attrs:
                    conds = []
                    if r_key == "if":
                        ConditionStore["if"] = value
                        conds.append(value)
                    elif r_key == "elif":
                        if ConditionStore["if"] == None:
                            raise RuntimeError("elif cannot be used before if")

                        dom.attrib.pop(":elif")
                        if ConditionStore["elif"] == None:
                            ConditionStore["elif"] = []

                        ConditionStore["elif"].append(value)

                        if "not" in ConditionStore["if"]:
                            conds.append(" ".join([ item.strip() for item in ConditionStore["if"].split("not") ]))
                        else:
                            conds.append("not " + ConditionStore["if"])

                        for ei_cond in ConditionStore["elif"]:
                            if not ei_cond == ConditionStore["elif"][-1]:
                                if "not" in ei_cond:
                                    ei_cond = " ".join([ item.strip() for item in ei_cond.split("not") ])
                                else:
                                    ei_cond = "not " + ei_cond

                            conds.append(ei_cond)
                    elif r_key == "else":
                        if ConditionStore["if"] == None:
                            raise RuntimeError("else cannot be used before if")

                        dom.attrib.pop(":else")

                        if "not" in ConditionStore["if"]:
                            conds.append(" ".join([ item.strip() for item in ConditionStore["if"].split("not") ]))
                        else:
                            conds.append("not " + ConditionStore["if"])

                        if ConditionStore["elif"] is not None:
                            for ei_cond in ConditionStore["elif"]:
                                if "not" in ei_cond:
                                    ei_cond = " ".join([ item.strip() for item in ei_cond.split("not") ])
                                else:
                                    ei_cond = "not " + ei_cond

                                conds.append(ei_cond)

                    dom.attrib[":if"] = " and ".join(conds)
                elif r_key in loop_attrs:
                    for child in dom.getchildren():
                        if not ":for" in child.attrib.keys():
                            child.attrib[":for-item"] = None

        for child in dom.getchildren():
            Parser.change_dom_for_template(child)

        return dom

    @staticmethod
    def change_template_for_format(template:str) -> str:
        return template.strip().replace("{ ", "{").replace(" }", "}")
