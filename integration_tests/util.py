import inspect


def output_str(s: str) -> str:
    clean_str = inspect.cleandoc(s)
    return f"{clean_str}\n"
