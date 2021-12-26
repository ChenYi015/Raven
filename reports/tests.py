def add(x, y):
    """Get the sum of two numbers.

    Args:
        x (float): number x
        y (float): number y

    Returns:
        float: the sum of two numbers
    """
    return x + y

def test_add():
    assert add(1, 2) == 3
