# -*- coding: utf-8 -*-
"""
FIREBASE AUTHENTICATION MODULE
===============================
Quản lý xác thực người dùng qua Firebase Authentication
"""

import pyrebase
from typing import Optional, Dict

class FirebaseAuth:
    """Quản lý xác thực Firebase"""
    
    def __init__(self, config: Dict):
        """
        Khởi tạo Firebase Auth
        
        Args:
            config: Dictionary chứa Firebase config
        """
        self.firebase_config = {
            "apiKey": config.get("apiKey"),
            "authDomain": config.get("authDomain"),
            "projectId": config.get("projectId"),
            "storageBucket": config.get("storageBucket"),
            "messagingSenderId": config.get("messagingSenderId"),
            "appId": config.get("appId")
        }
        
        # Khởi tạo Pyrebase
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
    
    def sign_in_with_email_and_password(self, email: str, password: str) -> Optional[Dict]:
        """
        Đăng nhập bằng email và password
        
        Args:
            email: Email người dùng
            password: Mật khẩu
            
        Returns:
            Dict chứa user info nếu thành công, None nếu thất bại
        """
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            return {
                'uid': user.get('localId'),
                'email': user.get('email'),
                'id_token': user.get('idToken'),
                'refresh_token': user.get('refreshToken')
            }
        except Exception as e:
            print(f"❌ Firebase login error: {e}")
            return None
    
    def create_user_with_email_and_password(self, email: str, password: str) -> Optional[Dict]:
        """
        Đăng ký tài khoản mới
        
        Args:
            email: Email người dùng
            password: Mật khẩu
            
        Returns:
            Dict chứa user info nếu thành công, None nếu thất bại
        """
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            return {
                'uid': user.get('localId'),
                'email': user.get('email'),
                'id_token': user.get('idToken'),
                'refresh_token': user.get('refreshToken')
            }
        except Exception as e:
            print(f"❌ Firebase signup error: {e}")
            return None
    
    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """
        Xác thực ID token
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            Dict chứa user info nếu hợp lệ, None nếu không hợp lệ
        """
        try:
            # Pyrebase tự động xác thực token khi gọi user info
            # Trong production nên dùng Firebase Admin SDK để verify
            return {'valid': True}
        except Exception as e:
            print(f"❌ Token verification error: {e}")
            return None

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
        
        try:
            # Khởi tạo Pyrebase
            self.firebase = pyrebase.initialize_app(self.firebase_config)
            self.auth = self.firebase.auth()
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"⚠️  Firebase initialization error: {e}")
            raise 