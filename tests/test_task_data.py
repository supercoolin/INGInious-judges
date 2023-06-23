from task_common import TaskData, task_dir_to_TaskData, student_code_generate, student_code_validate
from pathlib import Path
import unittest
import os
import sys
project_root = os.path.dirname(sys.modules['__main__'].__file__)
test_data_path = os.path.join('.', 'tests', 'data')
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

        self.assertEquals(str(task_data.template), os.path.join(task_dir['root'], 'student', 'student_code.c.tpl'))
    
    def test_student_code_generate(self):

        task_dir = task_dirs[0]
        task_data = task_dir_to_TaskData(task_dir['root'], task_dir['build'], task_dir['libs'])
        file_names = [None, None]

        def generator(in_file: str, out_file: str):
            file_names[0] = in_file
            file_names[1] = out_file
        
        student_code_generate(task_data, generator)
        self.assertIsNotNone(task_data.student_code)
        self.assertNotIn(None, file_names)
        self.assertEquals(file_names[0], os.path.join(task_dir['root'], 'student', 'student_code.c.tpl'))
        self.assertEquals(file_names[1], os.path.join(task_dir['root'], 'student', 'student_code.c'))
        self.assertEquals(str(task_data.student_code), os.path.join(task_dir['root'], 'student', 'student_code.c')) 

    def test_student_code_validate(self):

        task_dir = task_dirs[0]
        task_data = task_dir_to_TaskData(task_dir['root'], task_dir['build'], task_dir['libs'])

        def generator(a: str, b: str):
            pass

        self.assertFalse(student_code_validate(task_data))
        student_code_generate(task_data, generator)
        self.assertFalse(student_code_validate(task_data))
        student_file_path = os.path.join(task_dir['root'], 'student', 'student_code.c')
        try:
            with open(student_file_path, 'w') as f:
                f.flush()
                self.assertTrue(student_code_validate(task_data))

        except AssertionError as e:
            os.remove(student_file_path)
            raise e from None
        finally:
            os.remove(student_file_path)

        
