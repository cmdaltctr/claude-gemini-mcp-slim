import unittest


class BasicTests(unittest.TestCase):
    def test_addition(self) -> None:
        self.assertEqual(1 + 1, 2)

    def test_subtraction(self) -> None:
        self.assertEqual(5 - 3, 2)


if __name__ == "__main__":
    unittest.main()
