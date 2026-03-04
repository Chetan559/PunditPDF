from fastapi import HTTPException, status


class PDFNotFoundError(HTTPException):
    def __init__(self, pdf_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF '{pdf_id}' not found",
        )


class PDFNotReadyError(HTTPException):
    def __init__(self, pdf_id: str, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PDF '{pdf_id}' is not ready yet. Current status: {current_status}",
        )


class FileTooLargeError(HTTPException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed size is {max_mb}MB",
        )


class InvalidFileTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are accepted",
        )


class QuizNotFoundError(HTTPException):
    def __init__(self, quiz_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz session '{quiz_id}' not found",
        )


class QuizAlreadyEvaluatedError(HTTPException):
    def __init__(self, quiz_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quiz '{quiz_id}' has already been evaluated",
        )


class ChatSessionNotFoundError(HTTPException):
    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found",
        )


class UserNotFoundError(HTTPException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )


class ProcessingError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {detail}",
        )