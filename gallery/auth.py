from typing import Annotated
from fastapi import Depends
from itsdangerous import URLSafeSerializer

from gallery import config


class Auth:
    
    def __init__(self, config: Annotated[config.Config, Depends(config.get_config)]):
        self.serializer = URLSafeSerializer(config.auth.secret_token, salt=config.auth.salt)
        self.username = config.admin.username
        self.password = config.admin.password

    def verify(self, username: str, password: str) -> bool:
        return username == self.username and password == self.password

    def generate_token(self, username: str) -> str:
        return self.serializer.dumps(username)
    
    def verify_token(self, token: str) -> str:
        try:
            return self.serializer.loads(token)
        except Exception:
            return None
