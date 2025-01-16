import unittest
import os
import sqlite3

class TestProjectPipeline(unittest.TestCase):
    
    db_file_path = os.getcwd() + '/data/charging_station.db'
    expected_row_count = 50
    expected_columns = [
        (0, 'state_name', 'TEXT', 0, None, 0),
        (1, 'count_of_ev_charging_stations', 'INTEGER', 0, None, 0),
        (2, 'count_of_ev_vehicles', 'INTEGER', 0, None, 0)
    ]
    
    def test_db_file_exists(self):
        self.assertTrue(os.path.exists(self.db_file_path))
        self.assertGreater(os.path.getsize(self.db_file_path), 0)

    def test_db_table_exist(self):
        conn = sqlite3.connect(self.db_file_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='charging_stations';")
        self.assertTrue(c.fetchone())
        conn.close()
    
    def test_check_db_rows(self):
        conn = sqlite3.connect(self.db_file_path)
        c = conn.cursor()
        c.execute("SELECT * FROM charging_stations;")
        rows = c.fetchall()
        self.assertEqual(len(rows), self.expected_row_count)
        conn.close()
    
    def test_check_all_db_rows_are_non_empty(self):
        conn = sqlite3.connect(self.db_file_path)
        c = conn.cursor()
        c.execute("SELECT * FROM charging_stations;")
        rows = c.fetchall()
        for row in rows:
            self.assertTrue(all(row))
        conn.close()

    def test_check_db_columns(self):
        conn = sqlite3.connect(self.db_file_path)
        c = conn.cursor()
        c.execute("PRAGMA table_info(charging_stations);")
        columns = c.fetchall()
        self.assertEqual(columns, self.expected_columns)
        conn.close()        

if __name__ == "__main__":
    unittest.main()