import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from agents.smart_router import (
    handle_deterministic_response,
    extract_clean_user_message,
    check_db_session,
    clear_login_attempts,
    LOGIN_STEP_0,
    reset_fsm,
)

class TestSmartRouter(unittest.TestCase):
    def test_smart_router_login_fsm(self):
        async def run_test():
            chat_id = "test_user_123"
            reset_fsm(chat_id)

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess:
                mock_sess.return_value = None
                resp = await handle_deterministic_response("hi", chat_id)
                self.assertEqual(resp, LOGIN_STEP_0)

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess:
                mock_sess.return_value = None
                resp = await handle_deterministic_response("teacher", chat_id)
                self.assertEqual(resp, "Enter your email:")

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess:
                mock_sess.return_value = None
                resp = await handle_deterministic_response("teacher@oamk.fi", chat_id)
                self.assertEqual(resp, "Enter your password:")

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess, \
                 patch("agents.smart_router.perform_teacher_login", new_callable=AsyncMock) as mock_login:
                mock_sess.return_value = None
                mock_login.return_value = (True, "Matti Meikalainen")
                resp = await handle_deterministic_response("secret123", chat_id)
                self.assertIn("Welcome, Matti Meikalainen!", resp)
                self.assertIn("Teacher Commands:", resp)

        asyncio.run(run_test())

    def test_smart_router_logged_in_menu(self):
        async def run_test():
            chat_id = "test_teacher_456"
            reset_fsm(chat_id)

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess, \
                 patch("mcp_server.get_risk_report_tool", new_callable=AsyncMock) as mock_risk:
                mock_sess.return_value = {"user_role": "teacher", "user_id": 1, "user_name": "Matti"}
                mock_risk.return_value = "RISK REPORT:\n🔴 Student A"
                resp = await handle_deterministic_response("risk", chat_id)
                self.assertIn("RISK REPORT:", resp)

        asyncio.run(run_test())

    def test_smart_router_complex_query_falls_back_to_llm(self):
        async def run_test():
            chat_id = "test_student_789"
            reset_fsm(chat_id)

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess:
                mock_sess.return_value = {"user_role": "student", "user_id": 2, "user_name": "Antti"}
                resp = await handle_deterministic_response("Can you explain how to transfer credits from another university?", chat_id)
                self.assertIsNone(resp)

        asyncio.run(run_test())

    def test_extract_clean_user_message_openclaw_lite(self):
        msgs = [
            {
                "role": "user",
                "content": (
                    "[Wed 2026-11-25 13:20 UTC] Conversation info: \u27e6openclaw:ctx\u27e7\n"
                    "```json\n"
                    '{"sender":{"id":"123456789","name":"TestUser","username":"testuser"}}\n'
                    "```\n\n"
                    "students"
                ),
            }
        ]
        self.assertEqual(extract_clean_user_message(msgs), "students")

    def test_extract_skips_trailing_internal_context_message(self):
        msgs = [
            {"role": "assistant", "content": "Enter your password:"},
            {
                "role": "user",
                "content": (
                    "[Wed 2026-11-25 13:28 UTC] Conversation info: \u27e6openclaw:ctx\u27e7\n"
                    "```json\n"
                    '{"sender":{"id":"123456789"}}\n'
                    "```\n\n"
                    "password123"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>\n"
                    "#session:1 2026-11-25 13:28 UTC User: james.white@oamk.fi\n"
                    "#session:2 2026-11-25 13:28 UTC OpenClaw: Enter your password:\n"
                    "<<<END_OPENCLAW_INTERNAL_CONTEXT>>>"
                ),
            },
        ]
        self.assertEqual(extract_clean_user_message(msgs), "password123")

    def test_extract_multipart_content_with_internal_context(self):
        msgs = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>\nUser: hi\n<<<END_OPENCLAW_INTERNAL_CONTEXT>>>",
                    },
                    {
                        "type": "text",
                        "text": (
                            "[Wed 2026-11-25 13:28 UTC] Conversation info: \u27e6openclaw:ctx\u27e7\n"
                            "```json\n"
                            '{"sender":{"id":"123456789"}}\n'
                            "```\n\n"
                            "james.white@oamk.fi"
                        ),
                    },
                ],
            }
        ]
        self.assertEqual(extract_clean_user_message(msgs), "james.white@oamk.fi")

    def test_teacher_analytics_and_curriculum(self):
        async def run_test():
            chat_id = "test_teacher_999"
            reset_fsm(chat_id)
            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess, \
                 patch("database.db_connector.get_course_analytics", new_callable=AsyncMock) as mock_an, \
                 patch("database.db_connector.get_curriculum", new_callable=AsyncMock) as mock_cur:
                mock_sess.return_value = {"user_role": "teacher", "user_id": 1, "user_name": "James White"}
                mock_an.return_value = [
                    {"course_code": "IN00CS84", "course_name": "Johdatus ohjelmointiin", "total_students": 5, "completed_count": 4, "avg_grade": 4.25}
                ]
                resp = await handle_deterministic_response("analytics", chat_id)
                self.assertIn("IN00CS84", resp)
                self.assertIn("4.2", resp)

                mock_cur.return_value = [
                    {"year_of_study": 1, "course_type": "mandatory", "course_code": "IN00CS84", "course_name": "Johdatus ohjelmointiin", "credit": 5}
                ]
                resp2 = await handle_deterministic_response("curriculum DIN2025S", chat_id)
                self.assertIn("Curriculum: DIN2025S", resp2)
                self.assertIn("IN00CS84", resp2)

        asyncio.run(run_test())

    def test_student_courses_vs_my_courses(self):
        async def run_test():
            chat_id = "test_student_888"
            reset_fsm(chat_id)
            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess, \
                 patch("database.db_connector.get_all_courses", new_callable=AsyncMock) as mock_all, \
                 patch("database.db_connector.get_student_enrollments", new_callable=AsyncMock) as mock_my:
                mock_sess.return_value = {"user_role": "student", "user_id": 1, "user_name": "John Smith"}
                mock_all.return_value = [
                    {"course_code": "IN00DL12", "course_name": "Web-sovellusten perusteet", "credit": 5, "year_of_study": 2}
                ]
                mock_my.return_value = [
                    {"course_code": "IN00EH18", "course_name": "Matematiikan perusteet 1", "credit": 3, "status": "completed", "grade": 4}
                ]
                resp_all = await handle_deterministic_response("courses", chat_id)
                self.assertIn("All OAMK Courses", resp_all)
                self.assertIn("IN00DL12", resp_all)

                resp_my = await handle_deterministic_response("my courses", chat_id)
                self.assertIn("My Courses", resp_my)
                self.assertIn("IN00EH18", resp_my)

        asyncio.run(run_test())

    def test_wrong_password_retry_and_rate_limit(self):
        async def run_test():
            chat_id = "test_rl_777"
            reset_fsm(chat_id)
            clear_login_attempts(chat_id)

            with patch("agents.smart_router.check_db_session", new_callable=AsyncMock) as mock_sess, \
                 patch("agents.smart_router.perform_teacher_login", new_callable=AsyncMock) as mock_login:
                mock_sess.return_value = None
                await handle_deterministic_response("teacher", chat_id)
                await handle_deterministic_response("james.white@oamk.fi", chat_id)

                # Wrong password -> stays in AWAITING_PASSWORD, shows remaining attempts
                mock_login.return_value = (False, "Wrong password")
                r1 = await handle_deterministic_response("bad1", chat_id)
                self.assertIn("Wrong password (4 attempts remaining)", r1)

                # Retry password directly without re-entering email -> succeeds + security tip
                mock_login.return_value = (True, "James White")
                r_ok = await handle_deterministic_response("password123", chat_id)
                self.assertIn("Welcome, James White!", r_ok)
                self.assertIn("Security tip", r_ok)

                # Trigger 5 failures -> rate-limit lockout
                await handle_deterministic_response("teacher", chat_id)
                await handle_deterministic_response("james.white@oamk.fi", chat_id)
                mock_login.return_value = (False, "Wrong password")
                for _ in range(4):
                    await handle_deterministic_response("wrong", chat_id)
                r_lock = await handle_deterministic_response("wrong", chat_id)
                self.assertIn("locked", r_lock.lower())

                # Subsequent message is blocked immediately
                r_blocked = await handle_deterministic_response("hi", chat_id)
                self.assertIn("Too many failed login attempts", r_blocked)

            clear_login_attempts(chat_id)

        asyncio.run(run_test())

    def test_session_ttl_expiry(self):
        async def run_test():
            chat_id = "test_ttl_555"
            reset_fsm(chat_id)

            with patch("database.db_connector.get_telegram_session", new_callable=AsyncMock) as mock_get, \
                 patch("database.db_connector.delete_telegram_session", new_callable=AsyncMock) as mock_del:
                mock_get.return_value = {
                    "chat_id": chat_id,
                    "user_role": "student",
                    "user_id": 1,
                    "user_name": "John Smith",
                    "session_age_sec": 25 * 3600,  # 25 hours (> 24h TTL)
                }
                sess = await check_db_session(chat_id)
                self.assertIsNone(sess)
                mock_del.assert_awaited_once_with(chat_id)

                # Next deterministic response notifies user about expiry
                mock_get.return_value = None
                resp = await handle_deterministic_response("my courses", chat_id)
                self.assertIn("session expired", resp.lower())

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
