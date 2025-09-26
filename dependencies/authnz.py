from dependencies.authn import authenticated_user
from fastapi import Depends, HTTPException , status
from typing import Annotated, Any

def has_roles(roles):
  def check_roles( 
      vendor: Annotated[Any, Depends(authenticated_user)]):
      if not vendor["roles"] in roles:
        raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail=f"Access denied",
        )
  return check_roles