import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from agents.smart_router import handle_deterministic_response, LOGIN_STEP_0, reset_fsm

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

if __name__ == "__main__":
    unittest.main()
