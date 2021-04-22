# -*- coding: utf-8 -*-

event_attrs = [ "click", "doubleClick", "change", "input" ]
value_attrs = [ "model" ]
value_attrs_real = {
    "model": "value"
}

class VirtualEventer:
    def __init__(self, comp, event_name:str):
        self.comp = comp
        self.__method = getattr(comp, event_name)

    def call(self, event):
        self.__method(event)
        self.comp.render()

class VirtualDOM:
    def __init__(self, component, real_dom):
        if "id" in real_dom.attrs:
            real_dom.removeAttribute("id")

        self.comp = component
        self.virt_dom = real_dom.cloneNode(False)
        if self.check_if_copy_text(real_dom):
            self.virt_dom.innerText = real_dom.firstChild.nodeValue

        self.real_dom = real_dom

        self.children = []
        for child in [ item for item in  real_dom.childNodes if hasattr(item, "tagName") ]:
            # check dom contains cond/loop
            if ":if" in child.attrs:
                self.children.append(VirtualCondition(component, child))
            elif ":for" in child.attrs:
                if not ":for" in self.virt_dom.attrs:
                    self.children.append(VirtualLoop(component, child))
            elif ":for-item" in child.attrs:
                pass
            else:
                self.children.append(VirtualDOM(component, child))

        self.bind_event = True

    def check_if_copy_text(self, real_dom) -> bool:
        try:
            real_dom.firstChild.nodeValue
            return (
                not real_dom.parentNode.tagName.lower().endswith("-app") or\
                not ":for" in real_dom.attrs or\
                not ":for-item" in real_dom.attrs
            )
        except:
            return False

    def render(self, format_vars:dict = None):
        for key in self.real_dom.attrs:
            if key.startswith(":"):
                self.real_dom.removeAttribute(key)

        if format_vars == None:
            format_vars = {}
            for p_name in self.comp.current_parameters:
                format_vars[p_name] = self.comp.current_parameters[p_name]
            
            for d_name in self.comp.current_datas:
                format_vars[d_name] = self.comp.current_datas[d_name]

        if "{" in self.virt_dom.innerText and "}" in self.virt_dom.innerText:
            self.real_dom.innerText = self.virt_dom.innerText.format(**format_vars)

        for a_name in self.virt_dom.attrs:
            a_val = self.virt_dom.attrs[a_name]

            if a_name.startswith(":"):
                a_name_real = a_name[1:]

                if self.bind_event and a_name_real in event_attrs:
                    self.real_dom.bind(a_name_real, self.comp.methods[a_val].call)
                elif a_name_real in value_attrs:
                    self.real_dom.setAttribute(value_attrs_real[a_name_real], a_val.format(**format_vars))
            else:
                self.real_dom.setAttribute(a_name, a_val)

        for child in self.children:
            child.render()

        self.bind_event = False

# condition(if/elif/else)
class VirtualCondition:
    def __init__(self, comp, real_dom):
        self.vdom = VirtualDOM(comp, real_dom)
        self.cond = self.vdom.virt_dom.getAttribute(":if")
        self.comp = self.vdom.comp

    def render(self):
        exec_vars, exec_str = {}, ""
        for p_name, p_val in self.comp.current_parameters.items():
            exec_vars[p_name] = p_val
            exec_str += p_name + " = {" + p_name + "}\n"
        
        for d_name, d_val in self.comp.current_datas.items():
            exec_vars[d_name] = d_val
            exec_str += d_name + " = {" + d_name + "}\n"

        exec_str += f"global out\nout = ({self.cond})"
        exec(exec_str.format(**exec_vars))

        global out
        if out:
            self.vdom.virt_dom.style["display"] = ""
        else:
            self.vdom.virt_dom.style["display"] = "none"

        self.vdom.render(exec_vars)

# loop(for)
class VirtualLoopItem:
    def __init__(self, state_item:dict, comp, real_dom):
        self.vdom = VirtualDOM(comp, real_dom)
        self.state_item = state_item

    def render(self):
        self.vdom.render(self.state_item)

class VirtualLoop:
    def __init__(self, comp, real_dom, state_item:dict = None, state_keys:list = None):
        self.vdom = VirtualDOM(comp, real_dom)
        self.state = self.vdom.virt_dom.getAttribute(":for")
        self.state_item = state_item
        self.state_keys = state_keys
        self.comp = self.vdom.comp

    def render(self):
        exec_vars, exec_str = {}, ""
        for p_name, p_val in self.comp.current_parameters.items():
            exec_vars[p_name] = p_val
            exec_str += p_name + " = {" + p_name + "}\n"
        
        for d_name, d_val in self.comp.current_datas.items():
            exec_vars[d_name] = d_val
            exec_str += d_name + " = {" + d_name + "}\n"

        if not self.state_item == None:
            for state_key in self.state_keys:
                exec_vars[state_key] = self.state_item[state_key]
                exec_str += state_key + " = {" + state_key + "}\n"

        exec_str += "global state_source\nstate_source = " + self.state.split("in")[-1].strip()
        exec(exec_str.format(**exec_vars))
        global state_source

        self.vdom.real_dom.innerHTML = "".join([ self.vdom.real_dom.innerHTML for item in state_source ])

        state_keys = [ item.strip() for item in self.state.split("in")[0].strip().split(",") ]
        state_keys_exec = ",".join([ f"key_{idx + 1}" for idx in range(len(state_keys)) ])

        raw_children = [ item for item in self.vdom.real_dom.childNodes if hasattr(item, "tagName") ]
        for item, child in zip(state_source, raw_children):
            exec(f"global {state_keys_exec}\n{state_keys_exec} = item")
            state_item = {
                state_key: eval(f"key_{idx + 1}")
                for idx, state_key in enumerate(state_keys)
            }

            if ":for" in child.attrs:
                self.vdom.children.append(VirtualLoop(self.comp, child, state_item, state_keys))
            elif ":for-item" in child.attrs:
                self.vdom.children.append(VirtualLoopItem(state_item, self.comp, child))
            else:
                self.vdom.children.append(VirtualDOM(self.comp, child))

        self.vdom.render(exec_vars)
