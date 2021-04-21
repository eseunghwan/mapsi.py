# -*- coding: utf-8 -*-
import os, argparse, shutil
from . import __path__ as mapsi_path


template_requires = ["public", "src", "App.mapsi", "main.py"]
def init_mapsi(dest:str):
    # create dest if not exists
    if not os.path.exists(dest):
        os.mkdir(dest)

    # check if project already exists
    if set(template_requires).issubset(os.listdir(dest)):
        raise RuntimeError("project files already exist!")

    # copy template files
    template_source = os.path.join(mapsi_path[0], "template_files")
    for t_file in os.listdir(template_source):
        if t_file in ("__pycache__"):
            continue

        t_path = os.path.join(template_source, t_file)
        if os.path.isdir(t_path):
            shutil.copytree(t_path, os.path.join(dest, t_file))
        else:
            shutil.copyfile(t_path, os.path.join(dest, t_file))

def build_mapsi(dest:str, make_dist:bool):
    from .core import Parser
    from glob import glob
    from brython import __path__ as brython_path

    source = os.getcwd()

    # check files exist
    if not set(template_requires).issubset(os.listdir(source)):
        raise RuntimeError("build can use in mapsi project directory!")

    # copy public files
    source_public_dir = os.path.join(source, "public")
    for public_file in os.listdir(source_public_dir):
        shutil.copyfile(os.path.join(source_public_dir, public_file), os.path.join(dest, public_file))

    # copy build files
    for build_file in os.listdir(os.path.join(mapsi_path[0], "build_files")):
        build_source_file = os.path.join(mapsi_path[0], "build_files", build_file)
        if os.path.isdir(build_source_file):
            shutil.copytree(build_source_file, os.path.join(dest, build_file))
        else:
            shutil.copyfile(build_source_file, os.path.join(dest, build_file))

    # copy brython files
    for script in ("brython.js", "brython_stdlib.js"):
        shutil.copyfile(os.path.join(brython_path[0], "data", script), os.path.join(dest, script))

    # copy project files
    shutil.copyfile(os.path.join(source, "main.py"), os.path.join(dest, "app_main.py"))
    if os.path.exists(os.path.join(source, "src", "router.py")):# router
        shutil.copyfile(os.path.join(source, "src", "router.py"), os.path.join(dest, "router.py"))

    if os.path.exists(os.path.join(source, "src", "assets")):# assets
        shutil.copytree(os.path.join(source, "src", "assets"), os.path.join(dest, "assets"))

    # load mapsi and compile to py
    Parser.load_mapsi(os.path.join(source, "App.mapsi")).render_to_file(os.path.join(dest, "App.py"))
    dest_views_file, dest_components_file = os.path.join(dest, "views.py"), os.path.join(dest, "components.py")
    with open(dest_views_file, "w", encoding = "utf-8") as dvfw:
        dvfw.write("")

        for idx, comp in enumerate(Parser.load_mapsi_from_directory(os.path.join(source, "src", "views"))):
            dvfw.write(comp.render(idx == 0))

    with open(dest_components_file, "w", encoding = "utf-8") as dcfw:
        dcfw.write("")

        for idx, comp in enumerate(Parser.load_mapsi_from_directory(os.path.join(source, "src", "components"))):
            dcfw.write(comp.render(idx == 0))

    if make_dist:# build modules by brython-cli
        os.chdir(dest)

        # build
        os.system("brython-cli --modules")

        # remove python files
        for py_file in glob(os.path.join(dest, "*.py"), recursive = False):
            os.remove(py_file)

        # remove unnecessary files
        os.remove(os.path.join(dest, "brython_stdlib.js"))

        os.chdir(source)

def serve_mapsi(cwd:str):
    import sys

    cur_cwd = os.getcwd()
    os.chdir(cwd)
    os.system(f"{sys.executable} -m http.server --bind=127.0.0.1")
    os.chdir(cur_cwd)


def main():
    parser = argparse.ArgumentParser(description = "Mapsi CLI")
    parser.add_argument("job", type = str, help = "job to execute(init, serve, dist)")
    parser.add_argument("--dest", type = str, help = "destination for job", default = ".")
    args = vars(parser.parse_args())

    job, dest = args["job"], args["dest"]
    if dest.startswith("./") or dest.startswith(".\\"):
        dest = dest[2:]
    elif dest.startswith("."):
        dest = dest[1:]

    if job == "init":
        if not os.path.isabs(dest):
            dest = os.path.join(os.getcwd(), dest)

        init_mapsi(dest)

    elif job in ("build", "serve"):
        if not os.path.isabs(dest):
            dest = os.path.join(os.getcwd(), "dist" if dest == "" else dest)

        if os.path.exists(dest):
            shutil.rmtree(dest)

        os.mkdir(dest)

        if job == "build":
            build_mapsi(dest, True)
        else:
            build_mapsi(dest, False)
            serve_mapsi(dest)
            
if __name__ == "__main__":
    import sys
    sys.exit(main())
