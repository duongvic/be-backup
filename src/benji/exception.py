#!/usr/bin/env python
# -*- encoding: utf-8 -*-


class BenjiException(Exception):
    pass


class UsageError(BenjiException, RuntimeError):
    pass


class InputDataError(BenjiException, RuntimeError):
    pass


class AlreadyLocked(BenjiException, RuntimeError):
    pass


class InternalError(BenjiException, RuntimeError):
    pass


class ConfigurationError(BenjiException, RuntimeError):
    pass


class ScrubbingError(BenjiException, IOError):
    pass


class BenjiError(BenjiException):
    message = "An unknown exception occurred"

    def __init__(self, code=None, message=None, cause=None):
        super().__init__()
        self.code = code
        self.message = message
        self.cause = cause

    def get_message(self, localized=True, with_cause=True):
        msg = self.message if localized else self.message
        if with_cause and self.cause is not None:
            msg = '{}. Reason: {}'.format(msg, str(self.cause))
        return msg

    def __str__(self):
        return self.get_message(localized=False)

    def __repr__(self):
        return self.get_message(localized=False)

    def to_json(self):
        result = {
            'message': self.message,
            'status_code': self.code
        }
        # if self.cause:
        #     LOG.error(self.cause)
        #     result['cause'] = str(self.cause)
        return result


class InvalidModelError(BenjiError):

    message = "The following values are invalid: %(errors)s."


class GRCPError(BenjiError):
    message = "Error"


class GRCPTimeoutError(BenjiError):
    message = "Error connecting to gRPC server"


class RuntimeError(BenjiError):
    message = "RunTime Error"
