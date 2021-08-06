def obscurify_secret(secret: str, visible_ratio: int = 3, obscured_char: str = "*") -> str:
    """ Get a partially visible "secret" string, only revealing the latter part of the input. """
    visible = len(secret) // visible_ratio
    return f"{obscured_char * visible * (visible_ratio - 1)}{secret[-visible:]}"
