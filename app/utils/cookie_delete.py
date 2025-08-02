from fastapi.responses import Response

def delete_access_token_cookie(response: Response) -> Response:
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
        secure=False
    )
    return response