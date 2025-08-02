from .security import (
    hash_password, verify_password, create_access_token,
    decode_access_token,verify_password_reset_token
    ,create_password_reset_token,authenticate_user
)
from .dependencies import get_current_user,get_current_user_id, get_async_db,get_current_teacher_user,get_teacher_and_check_student_access
from .exceptions import (
    CredentialsException,
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    raise_credentials_exception,
    raise_not_found_exception,
    raise_bad_request_exception,
    raise_forbidden_exception,
)
from .validators import is_valid_email, is_strong_password
from .cookie_delete import delete_access_token_cookie

__all__ = [
    "hash_password",
    "get_teacher_and_check_student_access",
    "create_password_reset_token",
    "authenticate_user",
    "verify_password_reset_token",
    "get_current_teacher_user",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_user_id",
    "get_async_db",
    "CredentialsException",
    "NotFoundException",
    "BadRequestException",
    "ForbiddenException",
    "raise_credentials_exception",
    "raise_not_found_exception",
    "raise_bad_request_exception",
    "raise_forbidden_exception",
    "is_valid_email",
    "is_strong_password",
    "delete_access_token_cookie",
]
