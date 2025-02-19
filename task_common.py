from typing import Optional, List, Callable, Any
from pathlib import Path
import yaml
import os
import logging
import subprocess, shlex, re, os, yaml
from dataclasses import dataclass
from itertools import chain
logging.basicConfig()
logger = logging.getLogger('JudgeAPI')
logger.setLevel('DEBUG')
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
    task_root: Path
    template: Path
    task: dict #Parsed task.yaml describing the task
    build_script: Optional[Path] #Used to store the optional scripts that are needed to compile the student's code
    lib_dirs: Optional[List[Path]] #Used to store the paths of the libraries and includes used by the task
    annex: Optional[List[Path]] #Used to store a list of paths with annex files
    student_code: Optional[Path] #Path to the student code

    

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
    dir_content = os.listdir(task_dir_path)
    dir_files = {str(f).lower():f for f in dir_content if os.path.isfile(os.path.join(task_dir_path, f))}
    dir_subdirs = {str(d).lower():d for d in dir_content if os.path.isdir(os.path.join(task_dir_path, d))}

    #check for mandatory files and subdirectories
    if "task.yaml" not in dir_files and "task.yml" not in dir_files:
        logger.warning(f"Could not find task.yaml in {str(task_dir_path)}")
        return False
    
    if "run" not in dir_files:
        logger.warning(f"Could not find run file in {task_dir_path}")
        return False
    
    if "student" not in dir_subdirs:
        logger.warning(f"Could not find student folder in {task_dir_path}. Maybe the tasks are too simple for using this API ?")
        return False
    
    #check the content of the student directory
    student_dir = os.path.join(task_dir_path, dir_subdirs['student'])
    student_dir_content_splitted = [str(c).lower().split('.') for c in os.listdir(student_dir)]
    student_dir_content_ext = [splitted[1:] for splitted in student_dir_content_splitted if len(splitted) > 1]
    if 'tpl' not in chain(*student_dir_content_ext):
        logger.warning(f"Could not find template file in {str(student_dir)}")
        return False
    
    logger.debug(f"Validated task directory {str(task_dir_path)}")
    return True

def task_dir_to_TaskData(task_dir_path: Path, build_script: Path=None, lib_dirs: List[Path]=None) -> TaskData:
    """
    @brief: Use a task directory to parse a task into a task dictionary

    @param task_dir_path: (Path) instance of a path object pointing to the target task directory to parse into an object

    @return TaskData: The TaskData
    """
    if not task_dir_validate(task_dir_path):
        logger.error(f"Invalid task directory: {task_dir_path}")
        raise ValueError("Invalid argument")

    TaskData_init_kwargs= {
        'task_root': None,
        'template': None,
        'task': None,
        'build_script': None,
        'lib_dirs': None,
        'annex': None,
        'student_code': None
    } 
    TaskData_init_kwargs['task_root'] = task_dir_path
    #validate build script
    if build_script and os.path.isfile(build_script):
        TaskData_init_kwargs['build_script'] = os.path.join(task_dir_path, build_script)
    elif build_script:
        logger.warning(f"Build script file {build_script} does not exist")
    
    #validate lib dirs
    if lib_dirs:
        valid_libs = []
        for p in lib_dirs:
            if os.path.isdir(p):
                valid_libs.append(os.path.join(task_dir_path, p))
            else:
                logger.warning(f"Library/include directory {p} does not exist")
        TaskData_init_kwargs['lib_dirs'] = valid_libs
    
    #discover files and folders
    task_dir_content = {str(content).lower():content for content in os.listdir(task_dir_path)}
    task_dir_files = {name:path for name, path in task_dir_content.items() if os.path.isfile(os.path.join(task_dir_path, path))}
    task_dir_subdirs = {name:path for name, path in task_dir_content.items() if os.path.isdir(os.path.join(task_dir_path, path))}

    #Guess the yaml extension to the task file and load it into a dict
    task_file = task_dir_files['task.yaml'] if 'task.yaml' in task_dir_files else task_dir_files['task.yml']
    with open(os.path.join(task_dir_path, task_file), 'r') as f:
        TaskData_init_kwargs['task'] = yaml.safe_load(f)

    student_dir_path = os.path.join(task_dir_path, task_dir_content['student'])
    
    #discover files and folders of the student directory
    student_dir_content = {str(content).lower():content for content in os.listdir(student_dir_path)}
    student_dir_files = {name:path for name, path in student_dir_content.items() if os.path.isfile(os.path.join(student_dir_path, path))}
    student_dir_subdirs = {name:path for name, path in student_dir_content.items() if os.path.isfile(os.path.join(student_dir_path, path))}

    #retrieve the template file and the annex files
    annex = []
    for fname, fpath in student_dir_files.items():
        splitted = fname.split('.')
        #TODO USE REGEX IN CASE OF MULTIPLE EXTENSIONS
        if len(splitted) > 1:
            ext = splitted[-1]
            if ext == 'tpl':
                TaskData_init_kwargs['template'] = Path(os.path.join(student_dir_path, fpath))
            elif fname != build_script:
                annex.append(Path(os.path.join(student_dir_path, fpath)))
        elif fname != build_script:
            annex.append(Path(os.path.join(student_dir_path, fpath)))
    if len(annex) > 0:
        TaskData_init_kwargs['annex'] = annex
    
    return TaskData(**TaskData_init_kwargs)


def student_code_generate(task: TaskData, generator: Callable[[str, str], None]):
    filename = task.template.name
    filename_components = filename.split(".")
    extension = filename_components[1] if len(filename_components) > 2 else ""
    output_name = f"{filename_components[0]}.{extension}"
    in_path = os.path.join(task.task_root, 'student', filename)
    out_path = os.path.join(task.task_root, 'student', output_name)
    generator(in_path, out_path)
    task.student_code = out_path
    logger.debug(f"Generated student code: {output_name}")



def student_code_validate(task: TaskData) -> bool:
    if task.student_code is None:
        logger.error("Called student code validate with no student code generated")
        return False
    elif not os.path.isfile(task.student_code):
        logger.error(f"Invalid file path for student code {task.student_code}")
        return False
    return True


def _command_and_feedback(task: TaskData, command: str, check_and_feedback: Callable[[int, str], bool]):
    """
    Wrapper around launching a command and setting feedback
    command: any command to be run using Popen
    check_and_feedback: a callable taking the status code of the process 
                        to be called by command and the output of said command, it does the feedback accordingly.
    """
    if(len(command) >= 0):
        p = subprocess.Popen(shlex.split(command.format(task.student_code)), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = p.communicate()[0].decode('utf-8')
        return check_and_feedback(p.returncode, output)
    return True

def student_code_pre_compile(task: TaskData, command: str, check_and_feedback: Callable[[int, str], None]):
    """
    The commands to be called before we even try to compile the student code
    task: structure containing the data related to the task we're testing
    command: a string containing the command necessary for the pre compilation step
    check_and_feedback: a callable taking the status code of the process 
                        to be called by command and the output of said command, it does the feedback accordingly.
    
    """
    return _command_and_feedback(task, command, check_and_feedback)


def student_code_compile(task: TaskData, command: str, check_and_feedback: Callable[[int, str, Optional[Path], Optional[List[Path]]], None]):
    """
    Performs the compilation of the student code and performs the test related to it
    task: structure containing the data related to the task we're testing
    command: a string containing the command necessary for the compilation step
    check_and_feedback: a callable taking the status code of the process 
                        to be called by command and the output of said command, it does the feedback accordingly.
    """
    if(len(command) >= 0):
        p = subprocess.Popen(shlex.split(command.format(task.student_code)), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = p.communicate()[0].decode('utf-8')
        return check_and_feedback(p.returncode, output)
    return True


def student_code_post_compile(task: TaskData, command: str, check_and_feedback: Callable[[int, str], None]):
    """
    The commands to be called after we know the compilation went well
    task: structure containing the data related to the task we're testing
    command: a string containing the command necessary for the extra compilation steps
    check_and_feedback: a callable taking the status code of the process 
                        to be called by command and the output of said command, it does the feedback accordingly.
    
    """
    return _command_and_feedback(task, command, check_and_feedback)

def student_code_test_execution(task: TaskData, test: Callable[[Any], None]):
    """
    Run the tests during the student code execution
    task: structure containing the data related to the task we're testing
    test: the function that will perform the tests and optionally give a feedback
    """
    pass

def student_code_test_external(task: TaskData, command: str, check_and_feedback: Callable[[int, str], None]):
    """
    Any supplementary test in pure python to run from the outside of the student code
    task: structure containing the data related to the task we're testing
    test: the function that will perform the tests and optionally give a feedback
    """
    return _command_and_feedback(task, command, check_and_feedback)



    
class FrameWorkBuilder:
    """
    This class handles the state between the steps of creating a task framework. First add the commands and functions
    then call the builder to get a task runner function. This allows for modularity as you can modify the state between
    successive calls to the build method
    """
    def __init__(self):

        self.pre_compile_pair = (None, None)
        self.compile_pair = (None, None)
        self.post_compile_pair = (None, None)
        self.test_pair = (None, None)
        self.test_external = (None, None)


    def set_pre_compile_pair(self, command: str, fun: Callable[[int, str], None]):

        self.pre_compile_pair = (command, fun)


    def set_compile_pair(self, command: str, fun: Callable[[int, str, Optional[Path], Optional[List[Path]]], None]):

        self.compile_pair = (command, fun)


    def set_post_compile_pair(self, command: str, fun: Callable[[int, str], None]):

        self.post_compile_pair = (command, fun)


    def set_test_pair(self, command: str, fun: Callable[[Any], None]):

        self.test_pair = (command, fun)


    def set_test_external(self, command: str, fun: Callable[[int, str], None]):

        self.test_external = (command, fun)

    def build_framework(self):
        def run_task(task_dir: Path):
            

    