from fastapi import HTTPException, status


class DashForgeError(Exception):
    def __init__(self, message: str, code: str = "dashforge_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def not_found(entity: str, entity_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": f"{entity} '{entity_id}' was not found."},
    )


def bad_request(message: str, code: str = "bad_request") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": code, "message": message},
    )

