import unittest


def add(x, y):
    """Get the sum of two numbers.

    Args:
        x (float): number x
        y (float): number y

    Returns:
        float: the sum of two numbers
    """
    return x + y


def inc(x):
    """Increase number by 1.

    :param x: Number to increase
    :return: Number increased by 1
    """
    return x + 1


class MyTestCase(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(1, 2), 3)

    def test_inc(self):
        self.assertEqual(inc(1), 2)


if __name__ == '__main__':
    unittest.main()
