from pathlib import Path
import shutil
import Dot_Matrix_Panel.global_variables as global_variables #Verstehe nicht, warum Dot_Matrix_Panel.global_varables sein muss, aber funktioniert nur so

project_dir = Path(global_variables.project_dir).resolve()

if not getattr(global_variables, "project_dir", None):
    raise RuntimeError("Project directory not set in global_variables.project_dir")

def _check_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(project_dir):
        raise PermissionError(f"Access denied: {path} is outside project directory.")
    return path

def copytree(src, dst, *args, **kwargs):
    _check_path(src)
    _check_path(dst)
    return shutil.copytree(src, dst, *args, **kwargs)

def move(src, dst, *args, **kwargs):
    _check_path(src)
    _check_path(dst)
    return shutil.move(src, dst, *args, **kwargs)

def rmtree(path, *args, **kwargs):
    _check_path(path)
    return shutil.rmtree(path, *args, **kwargs)

def copy(src, dst, *args, **kwargs):
    _check_path(src)
    _check_path(dst)
    return shutil.copy(src, dst, *args, **kwargs)

def copy2(src, dst, *args, **kwargs):
    _check_path(src)
    _check_path(dst)
    return shutil.copy2(src, dst, *args, **kwargs)
