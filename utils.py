def prettify_number(string: str) -> str:
    number: float = float(string)

    if number > 0:
        return "+{}".format(number)

    return str(number)
