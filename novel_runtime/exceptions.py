class NovelRuntimeError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ProjectNotFoundError(NovelRuntimeError):
    pass


class ChapterNotFoundError(NovelRuntimeError):
    pass


class StyleNotSetError(NovelRuntimeError):
    pass


class InvalidStateTransitionError(NovelRuntimeError):
    pass


class LLMOutputValidationError(NovelRuntimeError):
    pass


class LLMCallError(NovelRuntimeError):
    pass


class TokenBudgetExceededError(NovelRuntimeError):
    pass


class SnapshotNotFoundError(NovelRuntimeError):
    pass


class BibleVersionConflictError(NovelRuntimeError):
    pass


class AgentContractViolationError(NovelRuntimeError):
    pass


class StateHealthCriticalError(NovelRuntimeError):
    pass
