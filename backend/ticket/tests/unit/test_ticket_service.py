import unittest
import yaml
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from app.services.ticket_service import TicketService
from app.models.ticket import Ticket
from app.repositories.ticket_repository import TicketRepository
from app.core.external import EventInfo, AccountClient

class TestTicketService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Read the shared mock_data.yaml
        base_path = os.path.dirname(__file__)
        yaml_path = os.path.join(base_path, "../../../../scripts/mock_data.yaml")
        with open(yaml_path, "r") as f:
            cls.mock_data = yaml.safe_load(f)
        
        cls.user = cls.mock_data['users'][0]
        cls.first_ticket = cls.mock_data['tickets'][0]
        cls.first_event = cls.mock_data['events'][0]

    def setUp(self):
        # Mock dependencies
        self.repo = MagicMock(spec=TicketRepository)
        self.event_client = MagicMock()
        self.account_client = MagicMock(spec=AccountClient)
        
        # Instantiate Service with all required dependencies
        self.service = TicketService(self.repo, self.event_client, self.account_client)

    def test_create_ticket_success(self):
        # Setup repo and client mocks
        self.repo.get_by_transaction_id.return_value = None
        self.repo.get_active_ticket.return_value = None
        self.account_client.verify_user_exists.return_value = True
        
        self.service.create_ticket(
            self.user['user_id'], 
            self.first_event['id'], 
            "new_tx_id"
        )
        
        self.repo.create.assert_called_once()

    def test_void_ticket_success(self):
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.status = "unused"
        self.repo.get_by_id.return_value = mock_ticket
        
        result = self.service.void_ticket(self.first_ticket['id'])
        
        self.assertTrue(result)
        self.repo.delete.assert_called_once_with(mock_ticket)

    def test_calculate_distance(self):
        # Taipei 101 to Taipei Station (approx 5km)
        lat1, lon1 = 25.0339, 121.5644
        lat2, lon2 = 25.0478, 121.5170
        
        dist = self.service._calculate_distance(lat1, lon1, lat2, lon2)
        self.assertGreater(dist, 5000)
        self.assertLess(dist, 5100)

    def test_checkin_out_of_range(self):
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.status = "unused"
        mock_ticket.user_id = self.user['user_id']
        mock_ticket.event_id = self.first_event['id']
        self.repo.get_by_id.return_value = mock_ticket
        
        mock_event = MagicMock(spec=EventInfo)
        mock_event.latitude = 25.0339
        mock_event.longitude = 121.5644
        mock_event.checkin_radius_meters = 100
        mock_event.event_start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_event.event_end_time = datetime.now(timezone.utc) + timedelta(hours=1)
        self.event_client.get_event.return_value = mock_event
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            # Taipei Station (out of 100m range)
            self.service.checkin(self.first_ticket['id'], self.user['user_id'], 25.0478, 121.5170)
        
        self.assertEqual(cm.exception.status_code, 400)
        self.assertEqual(cm.exception.detail["code"], "OUT_OF_RANGE")

if __name__ == "__main__":
    unittest.main()
