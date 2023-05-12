import copy
import json
import os
import requests
import yaml

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from dateutil import parser
from enum import Enum
from typing import Optional, Any, Dict, List, Tuple


class CheckListItemStatus(Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class TrelloListType(Enum):
    BACKLOG = "backlog"
    DOING = "doing"
    DONE = "done"


class TrelloCardStatus(Enum):
    NOT_STARTED = "not started"
    CHECKLIST_IN_PROGRESS = "check list in progress"
    CHECKLIST_ALL_COMPLETE = "check list all complete"
    OVERDUE = "overdue"
    IDLE = "idle"
    WITH_ISSUE = "with issue"
    UNKNOWN = "unknown"


class TrelloCardIssue(Enum):
    MISSING_START_DATE = "missing start date"
    MISSING_DUE_DATE = "missing due date"
    MISSING_MEMBERS = "no one is assigned to the card"


@dataclass
class TrelloBoard:
    id: Optional[str] = None
    name: Optional[str] = None


class TrelloCheckListItem:
    def __init__(self, item_json):
        self.id = item_json["id"]
        self.name = item_json["name"]
        self.status = CheckListItemStatus(item_json["state"])
        due = item_json["due"]
        self.due_date = parser.parse(due) if due else None

    def __str__(self):
        return f"\t\t• {self.name}:\n\t\t\tstate: {self.status.value}\n\t\t\tdue date: {self.due_date}\n"

    def is_complete(self):
        return self.status == CheckListItemStatus.COMPLETE.value


@dataclass
class TrelloCheckList:
    id: str
    name: str
    checklist_items: List[TrelloCheckListItem] = None

    def is_complete(self):
        if not self.checklist_items:
            return False
        list(filter(lambda item: item.is_complete(), self.checklist_items)) == len(
            self.checklist_items
        )

    def __str__(self):
        content = "\t" + self.name + "\n"
        for item in self.checklist_items:
            content += str(item)
        return content


class TrelloCard:
    def __init__(self, card_json, trello_config):
        self.id = card_json["id"]
        self.name = card_json["name"]
        self.url = card_json["url"]
        self.checklist_ids = card_json["idChecklists"]
        self.checklists = []
        self.member_ids = card_json["idMembers"]
        self.due_date = parser.parse(card_json["due"]) if card_json["due"] else None
        self.start_date = (
            parser.parse(card_json["start"]) if card_json["start"] else None
        )
        self.last_activity_date = (
            parser.parse(card_json["dateLastActivity"])
            if card_json["dateLastActivity"]
            else None
        )
        self.issues = []
        self.close_summary = None
        self.prefix = None
        self.trello_config = trello_config

    def is_complete(self):
        if not self.checklists:
            return False
        return list(filter(lambda list: list.is_complete(), self.checklists)) == len(
            self.checklists
        )

    def is_overdue(self):
        if self.due_date:
            now = datetime.now(timezone.utc)
            return now > self.due_date
        return False

    def is_idle(self):
        if self.last_activity_date:
            now = datetime.now(timezone.utc)
            idle_threshold = self.trello_config.idle_threshold
            idle_day = idle_threshold // (24 * 60)
            idle_second = (idle_threshold - idle_day * 24 * 60) * 60
            return now > timedelta(idle_day, idle_second) + self.last_activity_date
        return False

    def get_issues(self) -> List[TrelloCardIssue]:
        issues = []
        if not self.start_date:
            issues.append(TrelloCardIssue.MISSING_START_DATE)
        if not self.due_date:
            issues.append(TrelloCardIssue.MISSING_DUE_DATE)
        if not self.member_ids:
            issues.append(TrelloCardIssue.MISSING_MEMBERS)
        self.issues = issues
        return issues

    def get_status(self, trello_config) -> TrelloCardStatus:
        if self.checklists:
            if self.is_complete():
                return TrelloCardStatus.CHECKLIST_ALL_COMPLETE
            elif self.is_idle():
                return TrelloCardStatus.IDLE
            elif self.is_overdue():
                return TrelloCardStatus.OVERDUE
            elif self.checklists and not self.is_complete():
                return TrelloCardStatus.CHECKLIST_IN_PROGRESS
        return TrelloCardStatus.UNKNOWN

    def get_last_update_difference(self):
        if self.last_activity_date and self.start_date:
            diff = self.last_activity_date - self.start_date
            return diff
        return None

    def __str__(self):
        content = f"{self.prefix}: {self.name}\n"
        if self.issues:
            content += "\tTask Creation Issues:\n"
            for issue in self.issues:
                content += "\t\t• " + issue.value + "\n"
        if self.checklists:
            for checklist in self.checklists:
                content += str(checklist)
        if self.close_summary:
            content += "\tClose Summary:\n" + self.close_summary
        return content


@dataclass
class TrelloUser:
    id: str
    full_name: str
    user_name: str


@dataclass
class TrelloList:
    id: Optional[str] = None
    name: Optional[str] = None
    tag: Optional[str] = None


class TrelloConfig:
    def __init__(self, config):
        self.user_name = config["user_name"]
        self.board = TrelloBoard(name=config["board_name"])
        self.idle_threshold = config["idle_threshold"]
        self.board_lists = {}
        for board_list in config["board_lists"]:
            board_list = TrelloList(name=board_list["name"], tag=board_list["tag"])
            tag = board_list.tag
            self.board_lists[board_list.name] = board_list
            if tag == TrelloListType.BACKLOG.value:
                self.backlog_list = board_list
            elif tag == TrelloListType.DOING.value:
                self.doing_list = board_list
            elif tag == TrelloListType.DONE.value:
                self.done_list = board_list


def trello_api_key_set() -> bool:
    return (
        True if os.getenv("TRELLO_API_KEY") and os.getenv("TRELLO_API_TOKEN") else False
    )


def trello_config_file_exists() -> bool:
    return os.getenv("TRELLO_CONFIG_FILE") and os.path.exists(
        os.getenv("TRELLO_CONFIG_FILE")
    )


class Trello:
    def __init__(self):
        self.read_trello_configuration()
        api_key = (os.getenv("TRELLO_API_KEY"),)
        api_token = os.getenv("TRELLO_API_TOKEN")
        self.url = "https://api.trello.com/1"
        self.query = {
            "key": api_key,
            "token": api_token,
        }
        self.headers = {"Accept": "application/json"}

        get_boards_url = f"{self.url}/members/{self.trello_config.user_name}/boards"
        response_json = self._send_api_request(action="GET", url=get_boards_url)
        for board_json in response_json:
            if board_json["name"] == self.trello_config.board.name:
                board_id = board_json["id"]
                self.trello_config.board.id = board_id
                lists = self.get_board_lists(board_id)
                # process all the lists contained in the board
                for list in lists:
                    list_name = list.name
                    id = list.id
                    self.trello_config.board_lists[list_name].id = id
                    if list_name == self.trello_config.backlog_list.name:
                        self.trello_config.backlog_list.id = id
                    elif list_name == self.trello_config.doing_list.name:
                        self.trello_config.doing_list.id = id
                    elif list_name == self.trello_config.done_list.name:
                        self.trello_config.done_list.id = id
                # process all the board members
                trello_users = self.get_board_members(board_id=board_id)
                self.trello_users = {}
                for trello_user in trello_users:
                    self.trello_users[trello_user.id] = trello_user
                break

    def read_trello_configuration(self):
        with open(os.getenv("TRELLO_CONFIG_FILE"), "r") as stream:
            try:
                config = yaml.safe_load(stream)
                self.trello_config = TrelloConfig(config)
            except yaml.YAMLError as exc:
                print(exc)

        self.trello_config = TrelloConfig(config)

    def _send_api_request(
        self,
        url: str,
        action: str,
        query: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Any:
        response = requests.request(
            action,
            url,
            params=query if query else self.query,
            headers=headers if headers else self.headers,
        )
        # if url.find("members") >= 0:
        # print(response.text, "\n\n")
        response_json = json.loads(response.text)
        return response_json

    def get_cards(self, board_id: str, filter: str = "all"):
        url = f"{self.url}/boards/{board_id}/cards/{filter}"
        response = requests.request("GET", url, params=self.query, headers=self.headers)

    def get_board_lists(self, board_id: str, filter: str = "all") -> List[TrelloList]:
        url = f"{self.url}/boards/{board_id}/lists/{filter}"
        response = requests.request("GET", url, params=self.query, headers=self.headers)
        response_json = json.loads(response.text)
        trello_lists = []
        for list in response_json:
            trello_list = TrelloList(id=list["id"], name=list["name"])
            trello_lists.append(trello_list)
        return trello_lists

    def get_board_members(self, board_id: str) -> List[TrelloUser]:
        url = f"{self.url}/boards/{board_id}/members"
        response_json = self._send_api_request(action="GET", url=url)
        users = []
        for user in response_json:
            trello_user = TrelloUser(
                id=user["id"], full_name=user["fullName"], user_name=user["username"]
            )
            users.append(trello_user)
        return users

    def get_checklists(self, card_id: str) -> List[TrelloCheckList]:
        url = f"{self.url}/cards/{card_id}/checklists"
        response_json = self._send_api_request(action="GET", url=url)
        if not response_json:
            return []
        checklists = []
        for checklist_json in response_json:
            checklist_id = checklist_json["id"]
            checklist_name = checklist_json["name"]
            checklist_items = []
            for item_json in checklist_json["checkItems"]:
                checklist_item = TrelloCheckListItem(item_json=item_json)
                checklist_items.append(checklist_item)
            checklists.append(
                TrelloCheckList(
                    id=checklist_id,
                    name=checklist_name,
                    checklist_items=checklist_items,
                )
            )
        return checklists

    def add_card_comment(self, card_id: str, comment: str):
        url = f"{self.url}/cards/{card_id}/actions/comments"
        query = copy.deepcopy(self.query)
        query["text"] = comment
        self._send_api_request(url=url, action="POST", query=query)

    def mark_card_as_complete(self, card_id: str):
        url = f"{self.url}/cards/{card_id}"
        query = copy.deepcopy(self.query)
        query["dueComplete"] = "true"
        self._send_api_request(action="PUT", url=url, query=query)

    def move_card_to_new_list(self, card_id: str, new_list_id: str):
        url = f"{self.url}/cards/{card_id}"
        query = copy.deepcopy(self.query)
        query["idList"] = new_list_id
        self._send_api_request(action="PUT", url=url, query=query)

    def format_date_diff(self, diff: datetime):
        days = diff.days
        hours = diff.seconds // 3600
        return f"{days} days, {hours} hours"

    def generate_close_summary(
        self, member_ids: List[str], time_delta: Optional[datetime]
    ) -> str:
        comment = ""
        if member_ids:
            comment += "Team member(s) who worked on the card:\n"
            for member_id in member_ids:
                comment += f"    {self.trello_users[member_id].full_name}\n"
        if time_delta:
            comment += f"It took {self.format_date_diff(time_delta)}.\n"
        comment += "        - Marked as done by AutoGPT"
        return comment

    def _handle_all_complete_cards(self, trello_cards: List[TrelloCard]):
        summary = ""
        if trello_cards:
            summary += f"- Completed Tasks That Are Moved to {self.trello_config.done_list.name}:\n"
            for idx, trello_card in enumerate(trello_cards):
                trello_card.prefix = f"Completed Task {(idx+1):>03}"
                member_ids = trello_card.member_ids
                diff = trello_card.get_last_update_difference()
                comment = self.generate_close_summary(
                    member_ids=member_ids, time_delta=diff
                )
                trello_card.close_summary = comment
                self.add_card_comment(card_id=card_id, comment=comment)
                self.mark_card_as_complete(card_id=card_id)
                self.move_card_to_new_list(
                    card_id=card_id, new_list_id=self.trello_config.done_list.id
                )
            summary += str(trello_card)
        return summary

    def _handle_overdue_cards(self, trello_cards: List[TrelloCard]):
        summary = ""
        if trello_cards:
            summary += "- Overdue Tasks:\n"
            for idx, trello_card in enumerate(trello_cards):
                trello_card.prefix = f"Overdue Task {(idx+1):>03}"
                summary += str(trello_card)
        return summary

    def _handle_idle_cards(self, trello_cards: List[TrelloCard]):
        summary = ""
        if trello_cards:
            summary += "- Tasks That Haven't Been Updated in a While:\n"
            for idx, trello_card in enumerate(trello_cards):
                trello_card.prefix = f"Idle Task {(idx+1):>03}"
                summary += str(trello_card)
        return summary

    def _handle_with_issue_cards(self, trello_cards: List[TrelloCard]):
        summary = ""
        if trello_cards:
            summary = "\n\n- Tasks That Need More Details:\n"
            for idx, trello_card in enumerate(trello_cards):
                trello_card.prefix = f"With Issue Task {(idx+1):>03}"
                summary += str(trello_card)
        return summary

    def _handle_in_progress_cards(self, trello_cards: List[TrelloCard]):
        summary = ""
        if trello_cards:
            summary = "- In Progress Tasks:\n"
            for idx, trello_card in enumerate(trello_cards):
                trello_card.prefix = f"In Progress Task {(idx+1):>03}"
                summary += str(trello_card)
        return summary

    def get_doing_tasks_status(self):
        url = f"{self.url}/lists/{self.trello_config.doing_list.id}/cards"
        response_json = self._send_api_request(url=url, action="GET")

        all_complete_list = []
        overdue_list = []
        idle_list = []
        with_issue_list = []
        in_progress_list = []
        for card_json in response_json:
            trello_card = TrelloCard(
                card_json=card_json, trello_config=self.trello_config
            )
            card_id = trello_card.id
            checklists = self.get_checklists(card_id)
            trello_card.checklists = checklists
            trello_card_status = trello_card.get_status(
                trello_config=self.trello_config
            )
            if trello_card_status == TrelloCardStatus.CHECKLIST_ALL_COMPLETE:
                all_complete_list.append(trello_card)
            elif trello_card_status == TrelloCardStatus.CHECKLIST_IN_PROGRESS:
                in_progress_list.append(trello_card)

            issues = trello_card.get_issues()
            if issues:
                with_issue_list.append(trello_card)
            elif trello_card_status == TrelloCardStatus.OVERDUE:
                overdue_list.append(trello_card)
            elif trello_card_status == TrelloCardStatus.IDLE:
                idle_list.append(trello_card)
        summary = ""
        summary += self._handle_all_complete_cards(all_complete_list)
        summary += self._handle_in_progress_cards(in_progress_list)
        summary += self._handle_overdue_cards(overdue_list)
        summary += self._handle_with_issue_cards(with_issue_list)
        summary += self._handle_idle_cards(idle_list)
        print(summary)
        return summary


board_id = "6457300c5e50939a3ef7d958"
card_id = "6457301eb285c607736d4634"
list_id = "6457300c5e50939a3ef7d960"
done_list_id = "6457300c5e50939a3ef7d961"
# rello.add_card_comment(card_id=card_id, comment="Marked as done by AutoGPT")
# trello = Trello()
# trello.get_doing_tasks_status()
# trello.move_card_to_new_list(card_id=card_id, new_list_id=done_list_id)
