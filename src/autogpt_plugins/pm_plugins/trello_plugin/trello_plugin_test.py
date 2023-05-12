import http.client
import json
import os
import requests
import unittest
from unittest.mock import patch
from unittest.mock import mock_open
from trello_plugin import (
    Trello,
    TrelloCard,
    trello_api_key_set,
    trello_config_file_exists,
)


MOCK_HOST = "MOCK_HOST"
MOCK_TRELLO_API_KEY = "test_trello_api_key"
MOCK_TRELLO_API_TOKEN = "test_trello_api_token"
MOCK_TRELLO_CONFIG_FILE = "trello_config.yml"
MOCK_DATA_LOCATION = "test_data"


def get_mock_config_location():
    config_dir = os.path.dirname(__file__)
    rel_path = f"{MOCK_DATA_LOCATION}/{MOCK_TRELLO_CONFIG_FILE}"
    abs_file_path = os.path.join(config_dir, rel_path)
    return abs_file_path


def load_test_data_json(json_file: str):
    json_file_path = os.path.join(
        os.path.dirname(__file__), os.path.join(MOCK_DATA_LOCATION, json_file)
    )
    with open(json_file_path) as json_file:
        json_data = json.loads(json_file.read())
        return json_data


class MockResponse:
    def __init__(self, test_data: str):

        self.text = json.dumps(load_test_data_json(test_data))

    def text(self):
        print(self.text)
        return self.text


class TestTrelloPlugin(unittest.TestCase):
    @unittest.mock.patch.dict(
        os.environ,
        {
            "TRELLO_API_KEY": MOCK_TRELLO_API_KEY,
            "TRELLO_API_TOKEN": MOCK_TRELLO_API_TOKEN,
            "TRELLO_CONFIG_FILE": get_mock_config_location(),
        },
    )
    @patch("requests.request")
    def setUp(self, mock_request) -> None:
        # mock get boards
        # mock get_board_lists
        # mock get_board_members
        mock_request.side_effect = [
            MockResponse("boards.json"),
            MockResponse("lists.json"),
            MockResponse("members.json"),
        ]
        self.trello = Trello()

    @unittest.mock.patch.dict(
        os.environ,
        {
            "TRELLO_API_KEY": MOCK_TRELLO_API_KEY,
            "TRELLO_API_TOKEN": MOCK_TRELLO_API_TOKEN,
        },
    )
    def test_api_key_set(self):
        self.assertTrue(trello_api_key_set())

    @unittest.mock.patch.dict(
        os.environ,
        {
            "TRELLO_CONFIG_FILE": get_mock_config_location(),
        },
    )
    def test_config_file_exists(self):
        self.assertTrue(trello_config_file_exists())

    # TODO
    def test_initialization(self):
        self.assertEqual(len(self.trello.trello_users), 1)
        self.assertEqual(self.trello.trello_config.doing_list.name, "Doing")
        self.assertEqual(self.trello.trello_config.backlog_list.name, "To Do")
        self.assertEqual(self.trello.trello_config.done_list.name, "Done")

    @patch("requests.request")
    @patch("http.client.HTTPSConnection.getresponse")
    def test_card(self, mock_getresponse, mock_request):
        mock_request.side_effect = [
            MockResponse("card_overdue_checklists.json")
        ]  # mock response for getting get_checklists for overdue card
        over_due_trello_card = TrelloCard(
            card_json=load_test_data_json("card_overdue.json"),
            trello_config=self.trello.trello_config,
        )
        over_due_trello_card.checklists = self.trello.get_checklists(
            card_id=over_due_trello_card.id
        )
        # check card status is overdue
        self.assertFalse(over_due_trello_card.is_complete())
        self.assertTrue(over_due_trello_card.is_overdue())
        self.assertFalse(over_due_trello_card.is_idle())
        # check card checklists
        self.assertEqual(len(over_due_trello_card.checklists), 2)
        # check card checklist items
        self.assertEqual(len(over_due_trello_card.checklists[0].checklist_items), 2)
        self.assertEqual(len(over_due_trello_card.checklists[1].checklist_items), 3)


if __name__ == "__main__":
    unittest.main()
