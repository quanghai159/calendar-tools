# SPEC: CRM MODULE - PART 2

> Tiếp theo từ SPEC_CRM_MODULE.md

---

## 3. CUSTOMER INTERACTIONS

### 3.1. Interaction Manager

**File:** `backend/crm/interaction_manager.py`

```python
# -*- coding: utf-8 -*-
"""
INTERACTION MANAGER
===================

Quản lý lịch sử tương tác với khách hàng

Functions:
- create_interaction(interaction_data) -> interaction_id
- get_interactions(customer_id, limit) -> list
- update_interaction(interaction_id, updates) -> bool
- delete_interaction(interaction_id) -> bool
- get_latest_interaction(customer_id) -> dict
- create_interaction_with_task(interaction_data, task_data) -> (interaction_id, task_id)
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class InteractionManager:
    def __init__(self, db):
        self.db = db

    def create_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """
        Tạo interaction mới

        Args:
            interaction_data: {
                'customer_id': str,
                'user_id': str,
                'interaction_type': str,  # call/email/meeting/zalo/telegram/visit
                'direction': str,         # inbound/outbound
                'subject': str,
                'content': str,
                'outcome': str,           # interested/not_interested/callback...
                'next_action': str,
                'next_action_date': str,
                'related_task_id': str,
                'related_quotation_id': str,
                'attachments': list,      # ['file1.pdf', 'file2.jpg']
                'duration_minutes': int,
                'interaction_date': str
            }

        Returns:
            interaction_id

        Side effects:
            - Update customer.last_contact_date
            - Increment customer.total_interactions
        """
        try:
            # Generate ID
            interaction_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            # Process attachments
            attachments = interaction_data.get('attachments', [])
            attachments_json = json.dumps(attachments) if attachments else None

            # Prepare record
            record = {
                'interaction_id': interaction_id,
                'customer_id': interaction_data['customer_id'],
                'user_id': interaction_data['user_id'],
                'interaction_type': interaction_data['interaction_type'],
                'direction': interaction_data.get('direction', 'outbound'),
                'subject': interaction_data.get('subject'),
                'content': interaction_data.get('content'),
                'outcome': interaction_data.get('outcome'),
                'next_action': interaction_data.get('next_action'),
                'next_action_date': interaction_data.get('next_action_date'),
                'related_task_id': interaction_data.get('related_task_id'),
                'related_quotation_id': interaction_data.get('related_quotation_id'),
                'attachments': attachments_json,
                'duration_minutes': interaction_data.get('duration_minutes'),
                'interaction_date': interaction_data.get('interaction_date') or now,
                'created_at': now
            }

            # Insert
            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO customer_interactions ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))

                # Update customer
                customer_id = interaction_data['customer_id']
                update_query = """
                    UPDATE customers
                    SET last_contact_date = ?,
                        total_interactions = total_interactions + 1,
                        next_follow_up_date = ?,
                        updated_at = ?
                    WHERE customer_id = ?
                """
                self.db.execute_update(conn, update_query, (
                    interaction_data.get('interaction_date') or now,
                    interaction_data.get('next_action_date'),
                    now,
                    customer_id
                ))

                conn.commit()

            print(f"✅ Interaction created: {interaction_id}")
            return interaction_id

        except Exception as e:
            print(f"❌ Error creating interaction: {e}")
            raise

    def get_interactions(
        self,
        customer_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử tương tác của khách hàng

        Returns:
            List of interactions (sorted by interaction_date DESC)
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT i.*,
                           u.display_name as user_name,
                           t.title as related_task_title,
                           q.quotation_number as related_quotation_number
                    FROM customer_interactions i
                    LEFT JOIN users u ON i.user_id = u.user_id
                    LEFT JOIN tasks t ON i.related_task_id = t.task_id
                    LEFT JOIN quotations q ON i.related_quotation_id = q.quotation_id
                    WHERE i.customer_id = ?
                    ORDER BY i.interaction_date DESC
                    LIMIT ? OFFSET ?
                """
                results = self.db.execute_query(conn, query, (customer_id, limit, offset))

                # Parse attachments
                for interaction in results:
                    if interaction['attachments']:
                        interaction['attachments'] = json.loads(interaction['attachments'])
                    else:
                        interaction['attachments'] = []

                return results

        except Exception as e:
            print(f"❌ Error getting interactions: {e}")
            return []

    def update_interaction(self, interaction_id: str, updates: Dict[str, Any]) -> bool:
        """Cập nhật interaction"""
        try:
            allowed_fields = [
                'subject', 'content', 'outcome', 'next_action', 'next_action_date',
                'related_task_id', 'related_quotation_id', 'attachments', 'duration_minutes'
            ]

            set_strs = []
            params = []

            for field in allowed_fields:
                if field in updates:
                    value = updates[field]

                    # Process attachments
                    if field == 'attachments' and isinstance(value, list):
                        value = json.dumps(value)

                    set_strs.append(f"{field} = ?")
                    params.append(value)

            if not set_strs:
                return False

            params.append(interaction_id)

            with self.db.get_connection() as conn:
                query = f"UPDATE customer_interactions SET {', '.join(set_strs)} WHERE interaction_id = ?"
                self.db.execute_update(conn, query, tuple(params))
                conn.commit()

            print(f"✅ Interaction updated: {interaction_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating interaction: {e}")
            return False

    def delete_interaction(self, interaction_id: str) -> bool:
        """Xóa interaction"""
        try:
            with self.db.get_connection() as conn:
                # Decrement total_interactions
                query_get = "SELECT customer_id FROM customer_interactions WHERE interaction_id = ?"
                result = self.db.execute_query(conn, query_get, (interaction_id,))

                if result:
                    customer_id = result[0]['customer_id']

                    # Delete interaction
                    query_del = "DELETE FROM customer_interactions WHERE interaction_id = ?"
                    self.db.execute_update(conn, query_del, (interaction_id,))

                    # Update count
                    query_update = """
                        UPDATE customers
                        SET total_interactions = total_interactions - 1
                        WHERE customer_id = ?
                    """
                    self.db.execute_update(conn, query_update, (customer_id,))

                    conn.commit()

            print(f"✅ Interaction deleted: {interaction_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting interaction: {e}")
            return False

    def get_latest_interaction(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Lấy interaction gần nhất"""
        try:
            interactions = self.get_interactions(customer_id, limit=1)
            return interactions[0] if interactions else None

        except Exception as e:
            print(f"❌ Error getting latest interaction: {e}")
            return None

    def create_interaction_with_task(
        self,
        interaction_data: Dict[str, Any],
        task_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Tạo interaction + task follow-up

        Example flow:
            1. Sales gọi điện cho khách
            2. Tạo interaction log cuộc gọi
            3. Tạo task follow-up: "Gửi báo giá cho khách A"

        Returns:
            (interaction_id, task_id)
        """
        try:
            # Create task first
            from task_management.simple_task_manager import SimpleTaskManager
            task_manager = SimpleTaskManager(self.db)

            task_id = task_manager.create_task(task_data)

            # Create interaction với link to task
            interaction_data['related_task_id'] = task_id
            interaction_id = self.create_interaction(interaction_data)

            print(f"✅ Created interaction + task: {interaction_id}, {task_id}")
            return (interaction_id, task_id)

        except Exception as e:
            print(f"❌ Error creating interaction with task: {e}")
            raise
```

---

## 4. CARE SCENARIOS & AUTOMATION

### 4.1. Scenario Manager

**File:** `backend/crm/scenario_manager.py`

```python
# -*- coding: utf-8 -*-
"""
SCENARIO MANAGER
================

Quản lý kịch bản chăm sóc khách hàng tự động

Functions:
- create_scenario(scenario_data) -> scenario_id
- add_scenario_step(scenario_id, step_data) -> step_id
- start_scenario(customer_id, scenario_id) -> tracking_id
- process_due_steps() -> int (số actions được thực hiện)
- pause_scenario(tracking_id) -> bool
- resume_scenario(tracking_id) -> bool
- cancel_scenario(tracking_id) -> bool
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class ScenarioManager:
    def __init__(self, db):
        self.db = db

    def create_scenario(self, scenario_data: Dict[str, Any]) -> str:
        """
        Tạo kịch bản chăm sóc

        Args:
            scenario_data: {
                'scenario_name': str,
                'scenario_description': str,
                'customer_segment': str,  # new_lead/warm_lead/hot_lead...
                'trigger_event': str,     # customer_created/first_contact...
                'is_active': bool,
                'created_by': str
            }

        Returns:
            scenario_id
        """
        try:
            scenario_id = f"scenario_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            record = {
                'scenario_id': scenario_id,
                'scenario_name': scenario_data['scenario_name'],
                'scenario_description': scenario_data.get('scenario_description'),
                'customer_segment': scenario_data.get('customer_segment'),
                'trigger_event': scenario_data.get('trigger_event'),
                'is_active': 1 if scenario_data.get('is_active', True) else 0,
                'created_by': scenario_data.get('created_by'),
                'created_at': now,
                'updated_at': now
            }

            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO customer_care_scenarios ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Scenario created: {scenario_id}")
            return scenario_id

        except Exception as e:
            print(f"❌ Error creating scenario: {e}")
            raise

    def add_scenario_step(self, scenario_id: str, step_data: Dict[str, Any]) -> str:
        """
        Thêm step vào scenario

        Args:
            scenario_id: ID scenario
            step_data: {
                'step_order': int,
                'step_name': str,
                'step_description': str,
                'step_type': str,         # auto_task/auto_notification/auto_message
                'delay_days': int,
                'delay_hours': int,
                'delay_from': str,        # scenario_start/previous_step
                'action_type': str,       # call/email/zalo...
                'template_id': str,       # Message template (nếu auto_message)
                'task_template_id': str,  # Task template (nếu auto_task)
                'is_required': bool
            }

        Returns:
            step_id
        """
        try:
            step_id = f"step_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            record = {
                'step_id': step_id,
                'scenario_id': scenario_id,
                'step_order': step_data['step_order'],
                'step_name': step_data['step_name'],
                'step_description': step_data.get('step_description'),
                'step_type': step_data['step_type'],
                'delay_days': step_data.get('delay_days', 0),
                'delay_hours': step_data.get('delay_hours', 0),
                'delay_from': step_data.get('delay_from', 'scenario_start'),
                'action_type': step_data.get('action_type'),
                'template_id': step_data.get('template_id'),
                'task_template_id': step_data.get('task_template_id'),
                'is_required': 1 if step_data.get('is_required', True) else 0,
                'created_at': now
            }

            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO scenario_steps ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Scenario step created: {step_id}")
            return step_id

        except Exception as e:
            print(f"❌ Error adding scenario step: {e}")
            raise

    def start_scenario(self, customer_id: str, scenario_id: str, created_by: str = None) -> str:
        """
        Bắt đầu scenario cho customer

        Returns:
            tracking_id

        Algorithm:
            1. Tạo tracking record
            2. Schedule step 1 (nếu có)
            3. Return tracking_id
        """
        try:
            tracking_id = f"tracking_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            record = {
                'tracking_id': tracking_id,
                'customer_id': customer_id,
                'scenario_id': scenario_id,
                'current_step_order': 0,
                'scenario_status': 'active',
                'started_at': now,
                'completed_at': None,
                'last_action_at': now,
                'created_by': created_by
            }

            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO customer_scenario_tracking ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Scenario started: {tracking_id}")

            # Process first step immediately if delay = 0
            self.process_next_step(tracking_id)

            return tracking_id

        except Exception as e:
            print(f"❌ Error starting scenario: {e}")
            raise

    def process_next_step(self, tracking_id: str) -> bool:
        """
        Process step tiếp theo trong scenario

        Algorithm:
            1. Load tracking & scenario
            2. Lấy step tiếp theo (current_step_order + 1)
            3. Check delay:
               - Nếu delay > 0 → Schedule for later
               - Nếu delay = 0 → Execute ngay
            4. Execute step:
               - auto_task → Tạo task từ template
               - auto_message → Gửi message từ template
               - auto_notification → Gửi notification
            5. Update tracking.current_step_order
            6. If no more steps → Mark completed
        """
        try:
            # Load tracking
            with self.db.get_connection() as conn:
                query = "SELECT * FROM customer_scenario_tracking WHERE tracking_id = ?"
                tracking = self.db.execute_query(conn, query, (tracking_id,))

                if not tracking or tracking[0]['scenario_status'] != 'active':
                    return False

                tracking = tracking[0]

                # Load next step
                next_step_order = tracking['current_step_order'] + 1
                step_query = """
                    SELECT * FROM scenario_steps
                    WHERE scenario_id = ? AND step_order = ?
                """
                steps = self.db.execute_query(conn, step_query, (tracking['scenario_id'], next_step_order))

                if not steps:
                    # No more steps, mark completed
                    update_query = """
                        UPDATE customer_scenario_tracking
                        SET scenario_status = 'completed',
                            completed_at = ?,
                            last_action_at = ?
                        WHERE tracking_id = ?
                    """
                    self.db.execute_update(conn, update_query, (
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        tracking_id
                    ))
                    conn.commit()
                    print(f"✅ Scenario completed: {tracking_id}")
                    return True

                step = steps[0]

                # Calculate execution time
                if step['delay_from'] == 'scenario_start':
                    base_time = datetime.fromisoformat(tracking['started_at'])
                else:  # previous_step
                    base_time = datetime.fromisoformat(tracking['last_action_at'])

                execution_time = base_time + timedelta(
                    days=step['delay_days'],
                    hours=step['delay_hours']
                )

                now = datetime.now()

                if execution_time <= now:
                    # Execute now
                    self._execute_step(tracking['customer_id'], step)

                    # Update tracking
                    update_query = """
                        UPDATE customer_scenario_tracking
                        SET current_step_order = ?,
                            last_action_at = ?
                        WHERE tracking_id = ?
                    """
                    self.db.execute_update(conn, update_query, (
                        next_step_order,
                        datetime.now().isoformat(),
                        tracking_id
                    ))
                    conn.commit()

                    print(f"✅ Executed step {next_step_order} for tracking {tracking_id}")

                    # Process next step immediately (recursive)
                    return self.process_next_step(tracking_id)
                else:
                    # Schedule for later
                    print(f"⏰ Step {next_step_order} scheduled for {execution_time}")
                    return True

        except Exception as e:
            print(f"❌ Error processing next step: {e}")
            return False

    def _execute_step(self, customer_id: str, step: Dict[str, Any]):
        """
        Execute một step trong scenario

        Args:
            customer_id: ID khách hàng
            step: Dict step data

        Side effects:
            - Tạo task (nếu auto_task)
            - Gửi message (nếu auto_message)
            - Gửi notification (nếu auto_notification)
        """
        try:
            step_type = step['step_type']

            if step_type == 'auto_task':
                # Tạo task từ template
                if step['task_template_id']:
                    self._create_task_from_template(customer_id, step)

            elif step_type == 'auto_message':
                # Gửi message từ template
                if step['template_id']:
                    self._send_message_from_template(customer_id, step)

            elif step_type == 'auto_notification':
                # Gửi notification
                self._send_notification(customer_id, step)

            print(f"✅ Executed step: {step['step_name']}")

        except Exception as e:
            print(f"⚠️  Error executing step: {e}")

    def _create_task_from_template(self, customer_id: str, step: Dict[str, Any]):
        """Tạo task từ template cho customer"""
        try:
            # Load customer
            from crm.customer_manager import CustomerManager
            customer_manager = CustomerManager(self.db)
            customer = customer_manager.get_customer(customer_id)

            if not customer:
                return

            # Use template
            from task_management.task_template_manager import TaskTemplateManager
            template_manager = TaskTemplateManager(self.db)

            # Calculate start_date (now + some hours)
            start_date = datetime.now() + timedelta(hours=2)

            task_data = {
                'user_id': customer['assigned_to'],
                'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
                'variables': {
                    'customer_name': customer['full_name'],
                    'customer_phone': customer['phone_number'],
                    'customer_email': customer['email']
                }
            }

            task_id = template_manager.use_template(step['task_template_id'], task_data)
            print(f"✅ Created task from scenario: {task_id}")

        except Exception as e:
            print(f"⚠️  Error creating task from template: {e}")

    def _send_message_from_template(self, customer_id: str, step: Dict[str, Any]):
        """Gửi message từ template cho customer"""
        try:
            # Load customer
            from crm.customer_manager import CustomerManager
            customer_manager = CustomerManager(self.db)
            customer = customer_manager.get_customer(customer_id)

            if not customer:
                return

            # Load template
            from crm.template_manager import TemplateManager
            template_manager = TemplateManager(self.db)
            template = template_manager.get_template(step['template_id'])

            if not template:
                return

            # Replace variables
            variables = {
                'customer_name': customer['full_name'],
                'company_name': customer['company_name'] or ''
            }

            message = template['content']
            for var_name, var_value in variables.items():
                message = message.replace(f"{{{var_name}}}", var_value)

            # Send via channel
            channel = step['action_type']  # zalo/telegram/email

            if channel == 'zalo' and customer['zalo_id']:
                from notifications.zalo_notifier import ZaloNotifier
                from utils.config_loader import ConfigLoader

                config = ConfigLoader.load_config()
                notifier = ZaloNotifier(config)
                notifier.send_message(customer['zalo_id'], message)
                print(f"✅ Sent Zalo message to {customer['full_name']}")

            elif channel == 'telegram' and customer['telegram_id']:
                from notifications.telegram_notifier import TelegramNotifier
                from utils.config_loader import ConfigLoader

                config = ConfigLoader.load_config()
                notifier = TelegramNotifier(config)
                notifier.send_notification(customer['telegram_id'], message)
                print(f"✅ Sent Telegram message to {customer['full_name']}")

            elif channel == 'email' and customer['email']:
                from notifications.email_notifier import EmailNotifier
                from utils.config_loader import ConfigLoader

                config = ConfigLoader.load_config()
                notifier = EmailNotifier(config)
                notifier.send_email(
                    customer['email'],
                    template.get('subject', 'Hunonic'),
                    message
                )
                print(f"✅ Sent email to {customer['full_name']}")

        except Exception as e:
            print(f"⚠️  Error sending message: {e}")

    def _send_notification(self, customer_id: str, step: Dict[str, Any]):
        """Gửi notification đơn giản"""
        try:
            # Load customer
            from crm.customer_manager import CustomerManager
            customer_manager = CustomerManager(self.db)
            customer = customer_manager.get_customer(customer_id)

            if not customer or not customer['assigned_to']:
                return

            # Send notification to assigned user
            message = f"📋 Scenario reminder: {step['step_name']} for {customer['full_name']}"

            from notifications.telegram_notifier import TelegramNotifier
            from utils.config_loader import ConfigLoader

            config = ConfigLoader.load_config()
            notifier = TelegramNotifier(config)

            # Get assigned user's telegram
            with self.db.get_connection() as conn:
                query = "SELECT telegram_user_id FROM users WHERE user_id = ?"
                user = self.db.execute_query(conn, query, (customer['assigned_to'],))

                if user and user[0].get('telegram_user_id'):
                    notifier.send_notification(user[0]['telegram_user_id'], message)
                    print(f"✅ Sent notification to user {customer['assigned_to']}")

        except Exception as e:
            print(f"⚠️  Error sending notification: {e}")

    def process_due_steps(self) -> int:
        """
        Process tất cả scenarios đến hạn

        Chạy bởi background job/cron mỗi 1 giờ

        Returns:
            Số steps được execute

        Algorithm:
            1. Query tất cả active trackings
            2. Với mỗi tracking:
               - Check xem step tiếp theo đã đến hạn chưa
               - Nếu rồi → process_next_step()
            3. Return count
        """
        try:
            count = 0

            with self.db.get_connection() as conn:
                query = """
                    SELECT tracking_id
                    FROM customer_scenario_tracking
                    WHERE scenario_status = 'active'
                """
                trackings = self.db.execute_query(conn, query)

            for tracking in trackings:
                if self.process_next_step(tracking['tracking_id']):
                    count += 1

            if count > 0:
                print(f"✅ Processed {count} scenario steps")

            return count

        except Exception as e:
            print(f"❌ Error processing due steps: {e}")
            return 0

    def pause_scenario(self, tracking_id: str) -> bool:
        """Tạm dừng scenario"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customer_scenario_tracking SET scenario_status = 'paused' WHERE tracking_id = ?"
                self.db.execute_update(conn, query, (tracking_id,))
                conn.commit()

            print(f"✅ Scenario paused: {tracking_id}")
            return True

        except Exception as e:
            print(f"❌ Error pausing scenario: {e}")
            return False

    def resume_scenario(self, tracking_id: str) -> bool:
        """Tiếp tục scenario"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customer_scenario_tracking SET scenario_status = 'active' WHERE tracking_id = ?"
                self.db.execute_update(conn, query, (tracking_id,))
                conn.commit()

            print(f"✅ Scenario resumed: {tracking_id}")

            # Process next step
            self.process_next_step(tracking_id)

            return True

        except Exception as e:
            print(f"❌ Error resuming scenario: {e}")
            return False

    def cancel_scenario(self, tracking_id: str) -> bool:
        """Hủy scenario"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customer_scenario_tracking SET scenario_status = 'cancelled' WHERE tracking_id = ?"
                self.db.execute_update(conn, query, (tracking_id,))
                conn.commit()

            print(f"✅ Scenario cancelled: {tracking_id}")
            return True

        except Exception as e:
            print(f"❌ Error cancelling scenario: {e}")
            return False


# Background job
def run_scenario_processor():
    """
    Cron job để process scenarios

    Chạy mỗi 1 giờ:
        0 * * * * python3 backend/crm/scenario_manager.py
    """
    from core.database_manager import DatabaseManager

    db = DatabaseManager("database/calendar_tools.db")
    manager = ScenarioManager(db)

    print(f"[{datetime.now()}] Running scenario processor...")
    count = manager.process_due_steps()
    print(f"[{datetime.now()}] Completed. Executed {count} steps.")

if __name__ == "__main__":
    run_scenario_processor()
```

---

## 5. MESSAGE TEMPLATES

### 5.1. Template Manager

**File:** `backend/crm/template_manager.py`

```python
# -*- coding: utf-8 -*-
"""
TEMPLATE MANAGER
================

Quản lý message templates

Functions:
- create_template(template_data) -> template_id
- get_template(template_id) -> dict
- get_all_templates(user_id, channel, category) -> list
- update_template(template_id, updates) -> bool
- delete_template(template_id) -> bool
- use_template(template_id, customer_id, variables) -> str (rendered message)
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

class TemplateManager:
    def __init__(self, db):
        self.db = db

    def create_template(self, template_data: Dict[str, Any]) -> str:
        """
        Tạo message template

        Args:
            template_data: {
                'user_id': str,  # NULL nếu shared
                'template_name': str,
                'template_description': str,
                'channel': str,  # email/zalo/telegram/sms
                'category': str,  # greeting/follow_up/quotation...
                'subject': str,  # Cho email
                'content': str,  # Nội dung (có variables: {customer_name}...)
                'variables_help': str,
                'is_shared': bool,
                'created_by': str
            }

        Returns:
            template_id
        """
        try:
            template_id = f"tmsg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            record = {
                'template_id': template_id,
                'user_id': template_data.get('user_id'),
                'template_name': template_data['template_name'],
                'template_description': template_data.get('template_description'),
                'channel': template_data['channel'],
                'category': template_data.get('category'),
                'subject': template_data.get('subject'),
                'content': template_data['content'],
                'variables_help': template_data.get('variables_help'),
                'is_shared': 1 if template_data.get('is_shared') else 0,
                'created_by': template_data.get('created_by'),
                'usage_count': 0,
                'created_at': now,
                'updated_at': now
            }

            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO message_templates ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Template created: {template_id}")
            return template_id

        except Exception as e:
            print(f"❌ Error creating template: {e}")
            raise

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Lấy template"""
        try:
            with self.db.get_connection() as conn:
                query = "SELECT * FROM message_templates WHERE template_id = ?"
                results = self.db.execute_query(conn, query, (template_id,))
                return results[0] if results else None

        except Exception as e:
            print(f"❌ Error getting template: {e}")
            return None

    def get_all_templates(
        self,
        user_id: str = None,
        channel: str = None,
        category: str = None,
        include_shared: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách templates

        Args:
            user_id: Lọc theo user
            channel: Lọc theo channel
            category: Lọc theo category
            include_shared: Có bao gồm shared templates không

        Returns:
            List of templates
        """
        try:
            with self.db.get_connection() as conn:
                conditions = []
                params = []

                if user_id:
                    if include_shared:
                        conditions.append("(user_id = ? OR is_shared = 1)")
                        params.append(user_id)
                    else:
                        conditions.append("user_id = ?")
                        params.append(user_id)
                else:
                    conditions.append("is_shared = 1")

                if channel:
                    conditions.append("channel = ?")
                    params.append(channel)

                if category:
                    conditions.append("category = ?")
                    params.append(category)

                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                query = f"SELECT * FROM message_templates{where_clause} ORDER BY usage_count DESC, created_at DESC"

                results = self.db.execute_query(conn, query, tuple(params))
                return results

        except Exception as e:
            print(f"❌ Error getting templates: {e}")
            return []

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Cập nhật template"""
        try:
            allowed_fields = [
                'template_name', 'template_description', 'channel', 'category',
                'subject', 'content', 'variables_help', 'is_shared'
            ]

            set_strs = []
            params = []

            for field in allowed_fields:
                if field in updates:
                    set_strs.append(f"{field} = ?")
                    params.append(updates[field])

            if not set_strs:
                return False

            set_strs.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(template_id)

            with self.db.get_connection() as conn:
                query = f"UPDATE message_templates SET {', '.join(set_strs)} WHERE template_id = ?"
                self.db.execute_update(conn, query, tuple(params))
                conn.commit()

            print(f"✅ Template updated: {template_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating template: {e}")
            return False

    def delete_template(self, template_id: str) -> bool:
        """Xóa template"""
        try:
            with self.db.get_connection() as conn:
                query = "DELETE FROM message_templates WHERE template_id = ?"
                self.db.execute_update(conn, query, (template_id,))
                conn.commit()

            print(f"✅ Template deleted: {template_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting template: {e}")
            return False

    def use_template(
        self,
        template_id: str,
        customer_id: str,
        variables: Dict[str, str] = None
    ) -> str:
        """
        Render template với variables

        Args:
            template_id: ID template
            customer_id: ID customer
            variables: Dict các biến bổ sung

        Returns:
            Rendered message

        Algorithm:
            1. Load template
            2. Load customer
            3. Merge variables: customer info + custom variables
            4. Replace {variable_name} trong content
            5. Update usage_count
            6. Return rendered message
        """
        try:
            # Load template
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            # Load customer
            from crm.customer_manager import CustomerManager
            customer_manager = CustomerManager(self.db)
            customer = customer_manager.get_customer(customer_id)

            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")

            # Build variables dict
            all_variables = {
                'customer_name': customer['full_name'],
                'customer_phone': customer['phone_number'] or '',
                'customer_email': customer['email'] or '',
                'company_name': customer['company_name'] or '',
                'customer_address': customer['address'] or ''
            }

            # Merge custom variables
            if variables:
                all_variables.update(variables)

            # Replace trong content
            message = template['content']
            subject = template['subject'] or ''

            for var_name, var_value in all_variables.items():
                message = message.replace(f"{{{var_name}}}", str(var_value))
                subject = subject.replace(f"{{{var_name}}}", str(var_value))

            # Update usage count
            with self.db.get_connection() as conn:
                query = "UPDATE message_templates SET usage_count = usage_count + 1 WHERE template_id = ?"
                self.db.execute_update(conn, query, (template_id,))
                conn.commit()

            print(f"✅ Template rendered: {template_id}")

            # Return với subject nếu là email
            if template['channel'] == 'email':
                return f"Subject: {subject}\n\n{message}"
            else:
                return message

        except Exception as e:
            print(f"❌ Error using template: {e}")
            raise
```

---

(Tiếp tục phần 3...)
