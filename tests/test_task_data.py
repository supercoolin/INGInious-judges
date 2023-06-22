from task_common import TaskData, task_dir_to_TaskData
from pathlib import Path
import unittest
import os
import sys
project_root = os.path.dirname(sys.modules['__main__'].__file__)
test_data_path = os.path.join('tests', 'data')
task_dirs = [
    {
        'root': Path(os.path.join(test_data_path, 'tasks', 'strcpy')),
        'build': Path(os.path.join(test_data_path, 'tasks', 'strcpy', 'student', 'Makefile')),
        'libs': [Path(os.path.join(test_data_path, 'tasks', 'strcpy', 'student', 'CTester'))]
    }
]

class TaskDataTestCase(unittest.TestCase):

    def setUp(self):
        pass 

    def test_task_dir_to_TaskData(self):
        task_dir = task_dirs[0]
        task_data = task_dir_to_TaskData(task_dir['root'], task_dir['build'], task_dir['libs'])
        self.assertIsNotNone(task_data)
        for prop in ['task', 'build_script', 'lib_dirs', 'annex']:
            self.assertIsNotNone(task_data.__dict__[prop], msg=f"Property {prop} is None !")

        
