import importlib

def load(path):
    class_path = path.split(".")
    module_path = ".".join(class_path[:-1])
    class_name = class_path[-1]

    module = importlib.import_module(module_path)

    return getattr(module,class_name)
