# Auto-GPT Trello Plugin 🤖

## Configuring Trello Plugin 🔧

The current Trello manipulations are focused on managing three lists: backlog tasks, doing tasks, and done tasks. Users need to provide list names for the backlog, doing, and done. The plugin configures the Trello board by reading a configuration YAML file. The file location is specified by `TRELLO_CONFIG_FILE` environment variable defined in the `.env` file. 


```yaml
name: Trello Configurations 🛠
user_name: 👤
  YOUR_USER_NAME
board_name: 📋
  YOUR_TRELLO_BOARD_NAME
board_lists: 📝
  - 
    name: YOUR_BACKLOG_LIST_NAME
    tag: backlog
  - 
    name: YOUR_DOING_LIST_NAME
    tag: doing
  - 
    name: YOUR_DONE_LIST_NAME
    tag: done 
idle_threshold: ⏱
  YOUR_IDLE_THRESHOLD_IN_MINUTES
supervisor_user_name: 👥
  SUPER_VISOR_USER_NAME
