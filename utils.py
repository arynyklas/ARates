from time import time


def get_float_timestamp() -> float:
    return time()


def prettify_number(string: str) -> str:
    number: float = float(string)

    if number > 0:
        return "+{}".format(number)

    return str(number)
