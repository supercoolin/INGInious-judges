import unittest
from tests.test_task_data import TaskDataTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TaskDataTestCase('test_task_dir_to_TaskData'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())