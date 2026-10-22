"""Public, secret-free errors for the Garmin integration."""


class GarminError(Exception):
    def __init__(self, code, message, status=502, retry_after=0):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.retry_after = retry_after
