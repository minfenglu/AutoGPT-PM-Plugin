# Auto-GPT Trello Plugin
## Configuring Trello Plugin 
Currently the Trello manipulations are focused on managing three lists: backlog tasks, doing tasks and done tasks. Users need to provide list names for backlog, doing and done. And the plugin configures the trello board by reading a configuration yaml file. The file location is specified by `TRELLO_CONFIG_FILE` environment variable defined in the `.env` file. 


```
name: Trello Configurations
user_name:
  YOUR_USER_NAME
board_name:
  YOUR_TRELLO_BOARD_NAME
board_lists:
  - 
    name: YOUR_BACKLOG_LIST_NAME
    tag: backlog
  - 
    name: YOUR_DOING_LIST_NAME
    tag: doing
  - 
    name: YOUR_DONE_LIST_NAME
    tag: done 
idle_threshold:
  YOUR_IDLE_THRESHOLD_IN_MINUTES
supervisor_user_name:
  SUPER_VISOR_USER_NAME
```