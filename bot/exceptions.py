class ResponseError(Exception):
    """Connection and other server problems"""
    pass


class RequestError(Exception):
    """Format or request problems"""
    pass


class WrongIndicator(Exception):
    """Wrong indicator name"""
    pass
