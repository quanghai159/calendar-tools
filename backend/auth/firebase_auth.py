# -*- coding: utf-8 -*-
"""
FIREBASE AUTHENTICATION MODULE
===============================
Quản lý xác thực người dùng qua Firebase Authentication
"""

import firebase_admin
from firebase_admin import credentials, auth
import requests
from typing import Optional, Dict

class FirebaseAuth:
    """Quản lý xác thực Firebase"""

    def __init__(self, config: Dict):
        """
        Khởi tạo Firebase Auth

        Args:
            config: Dictionary chứa Firebase config
        """
        # Tạo databaseURL từ projectId hoặc lấy từ config nếu có
        project_id = config.get("projectId")
        database_url = config.get("databaseURL") or f"https://{project_id}.default-rtdb.firebaseio.com"

        self.firebase_config = {
            "apiKey": config.get("apiKey"),
            "authDomain": config.get("authDomain"),
            "projectId": project_id,
            "storageBucket": config.get("storageBucket"),
            "messagingSenderId": config.get("messagingSenderId"),
            "appId": config.get("appId"),
            "databaseURL": database_url
        }

        self.api_key = config.get("apiKey")

        try:
            # Khởi tạo Firebase Admin SDK (chỉ khởi tạo 1 lần)
            if not firebase_admin._apps:
                # Không cần service account credentials cho Auth REST API
                firebase_admin.initialize_app()
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"⚠️  Firebase initialization error: {e}")
            # Không raise để app vẫn chạy được khi không có Firebase

    def sign_in_with_email_and_password(self, email: str, password: str) -> Optional[Dict]:
        """
        Đăng nhập bằng email và password sử dụng Firebase REST API

        Args:
            email: Email người dùng
            password: Mật khẩu

        Returns:
            Dict chứa user info nếu thành công, None nếu thất bại
        """
        try:
            # Sử dụng Firebase REST API để sign in
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                return {
                    'uid': data.get('localId'),
                    'email': data.get('email'),
                    'id_token': data.get('idToken'),
                    'refresh_token': data.get('refreshToken'),
                    'localId': data.get('localId'),  # Compatibility with old code
                    'idToken': data.get('idToken')    # Compatibility with old code
                }
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ Firebase login error: {error_message}")
                raise Exception(error_message)

        except Exception as e:
            print(f"❌ Firebase login error: {e}")
            raise

    def create_user_with_email_and_password(self, email: str, password: str) -> Optional[Dict]:
        """
        Đăng ký tài khoản mới sử dụng Firebase REST API

        Args:
            email: Email người dùng
            password: Mật khẩu

        Returns:
            Dict chứa user info nếu thành công, None nếu thất bại
        """
        try:
            # Sử dụng Firebase REST API để sign up
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                return {
                    'uid': data.get('localId'),
                    'email': data.get('email'),
                    'id_token': data.get('idToken'),
                    'refresh_token': data.get('refreshToken'),
                    'localId': data.get('localId'),  # Compatibility with old code
                    'idToken': data.get('idToken')    # Compatibility with old code
                }
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ Firebase signup error: {error_message}")
                raise Exception(error_message)

        except Exception as e:
            print(f"❌ Firebase signup error: {e}")
            raise

    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """
        Xác thực ID token sử dụng Firebase Admin SDK

        Args:
            id_token: Firebase ID token

        Returns:
            Dict chứa user info nếu hợp lệ, None nếu không hợp lệ
        """
        try:
            # Verify token using Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            return {
                'valid': True,
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email')
            }
        except Exception as e:
            print(f"❌ Token verification error: {e}")
            return None
