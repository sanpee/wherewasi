import unittest
from query import QueryParser

class QueryTestCase(unittest.TestCase):
  def setUp(self):
    pass        

  def tearDown(self):
    pass
    
  def test_Simple(self):
    q = QueryParser('(12.3,45.6) to 17:00 from 15:12 within 0.5km')
    self.assertEqual(q.position[0], 12.3, 'Query OK')
    self.assertEqual(q.position[1], 45.6, 'Query OK')

  def test_Reform(self):
    q = QueryParser('(12.3, 45.6) from 15:12 to 17:00 within 0.5km')
    self.assertEqual(q.reform(), '(12.3, 45.6) from 15:12 to 17:00 within 0.5km')
        
if __name__ == '__main__':
    unittest.main()