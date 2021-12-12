from fastapi import Header, HTTPException, status


async def get_token_header(internal_token: str = Header(...)) -> None:
    if internal_token != "allowed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Internal-Token header invalid")
