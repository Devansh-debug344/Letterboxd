import pytest
from fastapi.testclient import TestClient

def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/user/",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass123"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"

def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401
    assert "Wrong password" in response.json().get('detail')

def test_login_user_not_found(client):
    """Test login for non-existent user"""
    response = client.post(
        "/api/login",
        data={
            "username": "nonexistent",
            "password": "anypass"
        }
    )
    assert response.status_code == 404

def test_rate_limit_brute_force(client , clear_redis):
    """Test rate limiting on failed login attempts"""
    username = "bruteforcetest"
    
    # Create a user first
    client.post(
        "/api/user/",
        json={
            "username": username,
            "email": "brute@example.com",
            "password": "correctpass"
        }
    )
    
    # Try wrong password 5 times
    for i in range(5):
        response = client.post(
            "/api/login",
            data={
                "username": username,
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401
        
     
    # 6th attempt should be rate limited
    response = client.post(
        "/api/login",
        data={
            "username": username,
            "password": "wrongpass"
        }
    )
    print("status code is" , response.status_code)
    assert response.status_code == 429  # Too Many Requests

def test_refresh_token(client, test_user):
    """Test token refresh"""
    # Login first
    login_response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    assert login_response.status_code == 200
    
    login_data = login_response.json()
    
    refresh_token = login_data.get("refresh_token")
    
    # Use refresh token
    response = client.post(
        "/api/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    # assert "access_token" in data
    # assert "refresh_token" in data
    assert data.get("refresh_token") != refresh_token

def test_refresh_token_reuse_detection(client, test_user):
    """Test that reusing old refresh token triggers security lockout"""
    # Login
    login_response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    old_refresh_token = login_response.json().get("refresh_token")
    
   
    response1 = client.post(
        "/api/refresh",
        json={"refresh_token": old_refresh_token}
    )
    assert response1.status_code == 200
    assert response1.json().get("refresh_token") != old_refresh_token
    
    # Try to use old token again (should detect reuse)
    response2 = client.post(
        "/api/refresh",
        json={"refresh_token": old_refresh_token}
    )
    assert response2.status_code == 401
    assert "Token reuse detected" in response2.json().get('detail')

def test_logout(client, test_user):
    """Test logout"""
    # Login
    login_response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    access_token = login_response.json().get("access_token")
    
    # Logout
    response = client.post(
        "/api/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "Logged out" in response.json().get("message")

def test_logout_all(client, test_user):
    """Test logout from all devices"""
    # Login
    login_response = client.post(
        "/api/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    access_token = login_response.json().get("access_token")
    
    # Logout all
    response = client.post(
        "/api/logout-all",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "all sessions" in response.json().get("message").lower()



# def test_otp_send(client):
#     """Test OTP sending"""
#     response = client.post(
#         "/api/otp/send",
#         json={"phone_number": "+919876543210"}
#     )
#     assert response.status_code == 200
#     assert "OTP sent" in response.json()["message"]

# def test_otp_verify_wrong_code(client):
#     """Test OTP verification with wrong code"""
#     # Send OTP
#     client.post(
#         "/api/otp/send",
#         json={"phone_number": "+919876543210"}
#     )
    
#     # Try wrong code
#     response = client.post(
#         "/api/otp/verify",
#         json={"phone_number": "+919876543210", "code": "000000"}
#     )
#     assert response.status_code == 401
#     assert "Wrong OTP" in response.json()["detail"]