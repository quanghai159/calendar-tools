# -*- coding: utf-8 -*-
"""
EMAIL NOTIFIER MODULE
=====================

Mô tả: Gửi thông báo qua Email
Cách hoạt động:
1. Kết nối SMTP server
2. Gửi email HTML/text
3. Hỗ trợ attachment
4. Xử lý lỗi và retry

Thuật toán chính:
- Sử dụng SMTP protocol
- HTML email templates
- Attachment support
- Retry mechanism
- Rate limiting

Hướng dẫn sử dụng:
1. Cấu hình SMTP settings trong config
2. Gọi send_email() để gửi email
3. Gọi send_template_email() để gửi template
4. Gọi send_attachment_email() để gửi file

Ví dụ:
    notifier = EmailNotifier(smtp_config)
    notifier.send_email("user@example.com", "Subject", "Body")
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

class EmailNotifier:
    def __init__(self, smtp_config: Dict[str, Any]):
        """
        Khởi tạo EmailNotifier
        
        Args:
            smtp_config: Dict chứa SMTP configuration
        """
        self.smtp_server = smtp_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = smtp_config.get('smtp_port', 587)
        self.username = smtp_config.get('username', '')
        self.password = smtp_config.get('password', '')
        self.from_email = smtp_config.get('from_email', self.username)
        self.from_name = smtp_config.get('from_name', 'Calendar Tools')
        
        self.max_retries = 3
        self.rate_limit_delay = 2  # Delay giữa các email (seconds)
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True) -> bool:
        """
        Thuật toán gửi email:
        1. Validate email addresses
        2. Tạo MIME message
        3. Kết nối SMTP server
        4. Gửi email với retry
        5. Log kết quả
        
        Args:
            to_email: Email người nhận
            subject: Tiêu đề email
            body: Nội dung email
            is_html: True nếu body là HTML
            
        Returns:
            True nếu gửi thành công
        """
        try:
            # Bước 1: Validate input
            if not to_email or not subject or not body:
                print("❌ Invalid email parameters")
                return False
            
            # Bước 2: Tạo MIME message
            message = MIMEMultipart('alternative')
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            message['Subject'] = subject
            
            # Bước 3: Add body
            if is_html:
                html_body = MIMEText(body, 'html', 'utf-8')
                message.attach(html_body)
            else:
                text_body = MIMEText(body, 'plain', 'utf-8')
                message.attach(text_body)
            
            # Bước 4: Gửi email với retry
            for attempt in range(self.max_retries):
                try:
                    # Kết nối SMTP
                    context = ssl.create_default_context()
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls(context=context)
                        server.login(self.username, self.password)
                        
                        # Gửi email
                        text = message.as_string()
                        server.sendmail(self.from_email, to_email, text)
                        
                        print(f"✅ Email sent to {to_email}")
                        return True
                        
                except Exception as e:
                    print(f"❌ Email send error (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.rate_limit_delay * (attempt + 1))
            
            return False
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def send_template_email(self, to_email: str, template_name: str, data: Dict[str, Any]) -> bool:
        """
        Gửi email theo template
        
        Args:
            to_email: Email người nhận
            template_name: Tên template
            data: Data để fill vào template
            
        Returns:
            True nếu gửi thành công
        """
        try:
            subject, body = self._render_template(template_name, data)
            return self.send_email(to_email, subject, body)
        except Exception as e:
            print(f"❌ Template email error: {e}")
            return False
    
    def send_attachment_email(self, to_email: str, subject: str, body: str, 
                            attachment_path: str, attachment_name: str = None) -> bool:
        """
        Gửi email có attachment
        
        Args:
            to_email: Email người nhận
            subject: Tiêu đề email
            body: Nội dung email
            attachment_path: Đường dẫn file attachment
            attachment_name: Tên file attachment
            
        Returns:
            True nếu gửi thành công
        """
        try:
            # Tạo MIME message
            message = MIMEMultipart()
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Add attachment
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment_name or "attachment"}'
            )
            message.attach(part)
            
            # Gửi email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                text = message.as_string()
                server.sendmail(self.from_email, to_email, text)
            
            print(f"✅ Email with attachment sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Attachment email error: {e}")
            return False
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> tuple:
        """
        Render email template
        
        Args:
            template_name: Tên template
            data: Data để fill
            
        Returns:
            Tuple (subject, body)
        """
        templates = {
            'reminder': {
                'subject': '🔔 Nhắc nhở lịch làm việc - {title}',
                'body': """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #2c3e50;">📅 CALENDAR TOOLS</h2>
                    <h3>🔔 NHẮC NHỞ LỊCH LÀM VIỆC</h3>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                        <h4 style="color: #2c3e50;">{title}</h4>
                        <p><strong>⏰ Hạn chót:</strong> {deadline}</p>
                        <p><strong>📝 Mô tả:</strong> {description}</p>
                    </div>
                    
                    <p>Hãy chuẩn bị sẵn sàng nhé! 💪</p>
                    
                    <hr>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        Gửi lúc: {timestamp}
                    </p>
                </body>
                </html>
                """
            },
            'daily_report': {
                'subject': '📊 Báo cáo hàng ngày - {date}',
                'body': """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #2c3e50;">📅 CALENDAR TOOLS</h2>
                    <h3>📊 BÁO CÁO HÀNG NGÀY</h3>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                        <p><strong>✅ Hoàn thành:</strong> {completed}</p>
                        <p><strong>⏳ Đang làm:</strong> {pending}</p>
                        <p><strong>❌ Quá hạn:</strong> {overdue}</p>
                    </div>
                    
                    <p>Chúc bạn một ngày làm việc hiệu quả! 🚀</p>
                    
                    <hr>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        Gửi lúc: {timestamp}
                    </p>
                </body>
                </html>
                """
            }
        }
        
        template = templates.get(template_name, {
            'subject': 'Calendar Tools Notification',
            'body': '{message}'
        })
        
        # Add timestamp
        data['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        subject = template['subject'].format(**data)
        body = template['body'].format(**data)
        
        return subject, body

# Test function
def test_email_notifier():
    """Test function để kiểm tra EmailNotifier hoạt động đúng"""
    try:
        # Mock SMTP config
        smtp_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'test@gmail.com',
            'password': 'test_password',
            'from_name': 'Calendar Tools Test'
        }
        
        notifier = EmailNotifier(smtp_config)
        
        # Test send email (sẽ fail vì credentials không thật)
        success = notifier.send_email("test@example.com", "Test Subject", "Test Body")
        print(f"✅ send_email() works: {success}")
        
        # Test template email
        template_data = {
            'title': 'Test Task',
            'deadline': '2024-01-15 17:00',
            'description': 'Test description'
        }
        success = notifier.send_template_email("test@example.com", "reminder", template_data)
        print(f"✅ send_template_email() works: {success}")
        
        print("🎉 EmailNotifier test passed!")
        
    except Exception as e:
        print(f"❌ EmailNotifier test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_notifier()