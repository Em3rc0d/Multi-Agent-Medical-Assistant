class EAKError(Exception):
    """Base error for the contract-first kernel."""


class SchemaValidationError(EAKError):
    pass


class GraphValidationError(EAKError):
    pass


class ResolutionError(EAKError):
    pass


class PolicyDeniedError(EAKError):
    pass


class StateTransitionError(EAKError):
    pass
