"""Provider-neutral AI service exceptions."""


class AIAuthenticationError(RuntimeError):
    pass


class AIAuthorizationError(RuntimeError):
    pass


class AIBillingError(RuntimeError):
    pass


class AIRateLimitError(RuntimeError):
    pass


class AIServiceError(RuntimeError):
    pass


class AIResponseValidationError(AIServiceError):
    """A provider returned an unusable structure, eligible for one repair attempt."""
