from dateutil import parser

date_str = "2023-05-10T01:00:00.000Z"
date = parser.parse(date_str)
print(type(date))


from enum import Enum


class CheckListItemStatus(Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


print(CheckListItemStatus.COMPLETE.value)

print(CheckListItemStatus("incomplete"))

import yaml
import os
from dataclasses import dataclass
from enum import Enum


class TrelloListType(Enum):
    BACKLOG = "backlog"
    DOING = "doing"
    DONE = "done"


print(TrelloListType.BACKLOG.value)


begin_str = "2023-05-07T04:59:15.534Z"
end_str = "2023-05-09T05:04:16.467Z"
begin_date = parser.parse(begin_str)
end_date = parser.parse(end_str)
delta = end_date - begin_date
print("days:", delta.days, "seconds", delta.seconds)

config_dir = os.path.dirname(__file__)
rel_path = "configs/trello_configuration.yml"
abs_file_path = os.path.join(config_dir, rel_path)

with open(abs_file_path, "r") as stream:
    config = yaml.safe_load(stream)
    print(config)


class TrelloCheckListItem:
    def __init__(self, status):
        self.status = status

    def __str__(self):
        return f"\t\t• {self.name}:\n\t\t\tstate: {self.status.value}\n\t\t\tdue date: {self.due_date}\n"

    def is_complete(self):
        return self.status == "complete"


items = [TrelloCheckListItem("complete")] * 5 + [TrelloCheckListItem("Incomplete")] * 2
filtered_items = list(filter(lambda item: item.is_complete(), items))
print("filtered_items", len(filtered_items))
