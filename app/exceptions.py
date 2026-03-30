class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(BusinessException):
    """验证错误"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class NotFoundError(BusinessException):
    """资源未找到"""
    def __init__(self, message: str = "资源未找到"):
        super().__init__(message, status_code=404)


class AuthenticationError(BusinessException):
    """认证错误"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401)


class AuthorizationError(BusinessException):
    """授权错误"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403)


class ConflictError(BusinessException):
    """冲突错误（如资源已存在）"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, status_code=409)
