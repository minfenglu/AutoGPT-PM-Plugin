# Auto-GPT PM Plugin
The Auto-GPT PM Plugin 

Meet the AI-powered project manager bot - the one-stop-shop for managing Jira, Trello, Google Calendar and many more! Simplify complex tasks, assign deadlines, track progress, monitor budgets, and generate reports - all in one place. 


## 🔧 Plugin Installation

Follow these steps to configure the Auto-GPT PM Plugin:

### 1. Follow Auto-GPT-Plugins Installation Instructions
Follow the instructions as per the [Auto-GPT-Plugins/README.md](https://github.com/Significant-Gravitas/Auto-GPT-Plugins/blob/master/README.md)

### 2. Locate the `.env.template` file
Find the file named `.env.template` in the main `/Auto-GPT` folder.

### 3. Create and rename a copy of the file
Duplicate the `.env.template` file and rename the copy to `.env` inside the `/Auto-GPT` folder.

### 4. Edit the `.env` file
Open the `.env` file in a text editor. Note: Files starting with a dot might be hidden by your operating system.

### 5. Add PM configuration settings
Append the following configuration settings to the end of the file:

```ini

################################################################################
### AUTOGPTPM - TRELLO
################################################################################
TRELLO_API_KEY=YOUR_TRELLO_API_TOKEN
TRELLO_API_TOKEN=YOUR_TRELLO_API_KEY_HERE
TRELLO_CONFIG_FILE=YOUR_TRELLO_CONFIG_FILE_HERE
```

### 6. Allowlist Plugin
In your `.env` search for `ALLOWLISTED_PLUGINS` and add this Plugin:

```ini
################################################################################
### ALLOWLISTED PLUGINS
################################################################################

#ALLOWLISTED_PLUGINS - Sets the listed plugins that are allowed (Example: plugin1,plugin2,plugin3)
ALLOWLISTED_PLUGINS=AutoGPTPMPlugin
```
## 🧪 Test the Auto-GPT PM Plugin

Experience the plugin's capabilities by asking it to clean up the Doing Trello board, generate a summary and email the report (need to config the email plugin)

1. **Configure Auto-GPT:**
A sample `ai_settins.yaml` 
```
ai_goals:
- Generate status report of all doing tasks by calling get_doing_tasks_status
- Save the status report with the current timestamp in the file name
- Send an email with the saved status report as the attachment
- Terminate
ai_name: PM
ai_role: Organize
api_budget: 0.0
```



2. **Run Auto-GPT:**
   Launch Auto-GPT, which should use PM plugin to help you manage your projects!


## 🏗️ Collection of Plugins
- Trello 
- Jira (Under Development)
- Google Calendar (Under Development)