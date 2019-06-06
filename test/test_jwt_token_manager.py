from ibm_cloud_sdk_core import JWTTokenManager
import time
import jwt
import pytest

class JWTTokenManagerMockImpl(JWTTokenManager):
    def __init__(self, url=None, access_token=None):
        self.url = url
        self.access_token = access_token
        self.request_count = 0 # just for tests to see how  many times request was called
        super(JWTTokenManagerMockImpl, self).__init__(url, access_token, 'access_token')

    def request_token(self):
        self.request_count += 1
        current_time = int(time.time())
        token_layout = {
            "username": "dummy",
            "role": "Admin",
            "permissions": [
                "administrator",
                "manage_catalog"
            ],
            "sub": "admin",
            "iss": "sss",
            "aud": "sss",
            "uid": "sss",
            "iat": current_time + 3600,
            "exp": current_time
        }

        access_token = jwt.encode(token_layout, 'secret', algorithm='HS256', headers={'kid': '230498151c214b788dd97f22b85410a5'})
        response = {"access_token": access_token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "expiration": current_time,
                    "refresh_token": "jy4gl91BQ",
                    "from_token_manager": True
                   }
        return response

def test_get_token():
    url = "https://iam.cloud.ibm.com/identity/token"
    # Case 1:
    token_manager = JWTTokenManagerMockImpl(url, 'user_access_token')
    token = token_manager.get_token()
    assert token == token_manager.user_access_token

    # Case 2a:
    token_manager.set_access_token(None)
    token_manager.get_token()
    assert token_manager.token_info.get('expires_in') == 3600

    # Case 3, valid token present
    token_manager.token_info = {"access_token": "old_dummy",
                                "token_type": "Bearer",
                                "expires_in": 3600,
                                "expiration": time.time(),
                                "refresh_token": "jy4gl91BQ"
                               }
    token = token_manager.get_token()
    assert token == "old_dummy"

    # Case 2b, expired token:
    token_manager.expire_time = int(time.time()) - (13 * 3600)
    token_manager.time_to_live = 43200

    token = token_manager.get_token()
    assert token != "old_dummy"
    assert token_manager.request_count == 2

def test_is_token_expired():
    token_manager = JWTTokenManagerMockImpl(None, None)
    assert token_manager._is_token_expired() is True
    token_manager.time_to_live = 3600
    token_manager.expire_time = int(time.time()) + 6000
    assert token_manager._is_token_expired() is False
    token_manager.expire_time = int(time.time()) - 3600
    assert token_manager._is_token_expired()

def test_not_implemented_error():
    with pytest.raises(NotImplementedError) as err:
        token_manager = JWTTokenManager(None, None)
        token_manager.request_token()
    assert str(err.value) == 'request_token MUST be overridden by a subclass of JWTTokenManager.'
