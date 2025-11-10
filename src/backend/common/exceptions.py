from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """리소스를 찾을 수 없을 때"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(HTTPException):
    """인증되지 않은 사용자"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    """권한이 없을 때"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    """잘못된 요청"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
