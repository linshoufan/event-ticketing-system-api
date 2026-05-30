import unittest
import yaml
import os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_internal_key, CurrentUser
from app.core.external import get_event_client, EventInfo

class TestTicketAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Read the shared mock_data.yaml
        base_path = os.path.dirname(__file__)
        yaml_path = os.path.join(base_path, "../../../../scripts/mock_data.yaml")
        with open(yaml_path, "r") as f:
            cls.mock_data = yaml.safe_load(f)
        
        # Use plural 'users' as defined in YAML
        cls.user = cls.mock_data['users'][0]
        cls.first_ticket = cls.mock_data['tickets'][0]

    def setUp(self):
        self.client = TestClient(app)
        
        # Mock auth logic to avoid needing real JWT or Internal Key
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            user_id=self.user['user_id'], 
            role="employee"
        )
        app.dependency_overrides[verify_internal_key] = lambda: None
        
        # Mock DB Session
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        
        # Mock Event Service Client
        self.event_client = MagicMock()
        app.dependency_overrides[get_event_client] = lambda: self.event_client

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_my_tickets_api(self):
        # Mock Service return
        with patch("app.services.ticket_service.TicketService.get_user_tickets") as mock_service:
            mock_service.return_value = [
                {
                    "ticketId": self.first_ticket['id'],
                    "eventId": "ev_001",
                    "status": "unused",
                    "checkinAvailable": True
                }
            ]
            
            response = self.client.get("/v1/tickets")
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"][0]["ticketId"], self.first_ticket['id'])

    def test_issue_ticket_internal_api(self):
        # Test Internal API: POST /v1/internal/tickets
        with patch("app.services.ticket_service.TicketService.create_ticket") as mock_create:
            mock_ticket = MagicMock()
            mock_ticket.to_dict.return_value = {"ticketId": "new_tk"}
            mock_create.return_value = mock_ticket
            
            payload = {
                "userId": self.user['user_id'],
                "eventId": "ev_001",
                "transactionId": "tx_new"
            }
            
            # Internal API requires X-Internal-Key, but we've overridden verification
            response = self.client.post("/v1/internal/tickets", json=payload)
            
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["data"]["ticketId"], "new_tk")

if __name__ == "__main__":
    unittest.main()
