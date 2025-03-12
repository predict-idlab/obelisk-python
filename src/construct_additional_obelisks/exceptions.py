class AuthenticationError(Exception):
    """
    Error thrown specifically when an authentication call fails,
    usually this indicates an invalid token.
    """
    pass

class ObeliskError(Exception):
    """
    Catch-all Exception for any issue in this library code.
    """
    pass
