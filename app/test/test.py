import unittest

from ..app.worker import keyword_task, source_task, subtask_comment


class MyTestCase(unittest.TestCase):
    def test_something(self):
        source_task(115)
        #keyword_task(38)
        #subtask_comment(12990)

if __name__ == '__main__':
    unittest.main()
