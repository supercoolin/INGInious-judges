from typing import Optional
from pathlib import Path
import yaml
import os
import logging
LOG_FMT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('JudgeAPI')
"""
Task common, the file defining the API that will be used for the C judge system.

This API assumes the following course structure:


    course/
    |   task_folder/
    |   |   student/
    |   |   |   [lib_folders]
    |   |   |   [test files]
    |   |   |   [build files]
    |   |   |   template file
    |   |   |   annex file
    |   |   run
    |   |   task.yaml
    |   < ... >
    |   course.yaml
    |   run
    |   annex

Where annex files can be any file used by the course/task, and the elements between square brackets are optional
"""
@dataclass
class TaskData:
    template: Path
    task: dict #Parsed task.yaml describing the task
    build_script: Optional[Path] #Used to store the optional scripts that are needed to compile the student's code
    lib_dirs: Optional[list[Path]] #Used to store the paths of the libraries and includes used by the task
    annex: Optional[list[Path]] #Used to store a list of paths with annex files

    

def task_dir_validate(task_dir_path: Path) -> bool:
    """
    @brief: performs various checks ensure the task_dir contains everything needed for further work using this API 

    @param task_dir_path: (Path) instance of a path object pointing to the target task directory to check

    @return boolean: True if the task directory can be parsed by this API, False otherwise 
    """
    if not os.path.exists(task_dir_path):
        logger.debug(f"task path {str(task_dir_path)} does not exist")
        return False
    #list task files
    dir_content = os.listdir()
    dir_files = {str(f).lower():f for f in dir_content if os.path.isfile(f)}
    dir_subdirs = {str(d).lower():d for d in dir_content if os.path.isdir(d)}

    #check for mandatory files and subdirectories
    if "task.yaml" not in dir_files and "task.yml" not in dir_files:
        logger.debug(f"Could not find task.yaml in {str(task_dir_path)}")
        return False
    
    if "run" not in dir_files:
        logger.debug(f"Could not find run file in {task_dir_path}")
        return False
    
    if "student" not in dir_subdirs:
        logger.debug(f"Could not find student folder in {task_dir_path}. Maybe the tasks are too simple for using this API ?")
        return False
    
    #check the content of the student directory

    student_dir = os.path.join(task_dir_path, dir_subdirs['student'])
    student_dir_content_splitted = [str(c).to_lower().split('.') for c in os.listdir(student_dir)]
    student_dir_content_ext = [splitted[1] for c in student_dir_content_splitted if len(splitted) > 1]
    if 'tpl' not in student_dir_content_ext:
        logger.debug(f"Could not find template file in {str(student_dir)}")
        return False

    logger.debug(f"Validated task directory {str(task_dir_path)}")
    return True
    
    
    

     




    
    


def task_dir_to_obj(task_dir_path: Path) -> TaskData:
    """
    @brief: Use a task directory to parse a task into a task dictionary 
    """
    pass