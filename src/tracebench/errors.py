class TracebenchError(Exception):
    """Expected CLI failure with a safe, actionable message."""

class InputError(TracebenchError):
    """The source cannot be read within the declared bounds."""

class ContractError(TracebenchError):
    """A dataset contract is malformed or unsupported."""

class ArtifactError(TracebenchError):
    """A report is invalid, incompatible, or cannot be written."""
