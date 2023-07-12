# SlackHerokuDeployerBot
## Intent 
Use a Slack command to schedule a deployment reminder, list commits since the last deploy, and more by using the `Heroku Deploy App` (display name `Handy Dandy Heroku Deploy Helper`).


## Commands
The current `Heroku Deploy App` supports two commands.

### List commits
- `/commit-list <heroku_app_name> <item_filter>`
    - This command lists the commits that have been merged to `stable` since the last deploy to `<app_name>` that match `item_filter`.
    - Example: `/commit-list stp-instant-cd fee_collab` will return all commits merged to `stable` since the last deploy to `stp-instant-cd` that touched any files in `fee_collab`.


### Get latest commit
- `/latest-deploy <heroku_app_name>`
    - This command returns the latest commit that was deployed to `<heroku_app_name>`.
    - Example: `/latest-deploy stp-instant-cd` will return the most recent commit associated with the last deploy to `stp-instant-cd`.


### Deploy reminder
- `/deploy-reminder [in] <minutes-til-reminder> <optional-notification-recipients>`
    - This command sets up a scheduled reminder to deploy after `<minutes-til-reminder>` minutes have passed, notifying the original creator of the reminder as well as optionally notifying a specified tagged teammate/team.
    - Example: `/deploy-reminder 30 @task-automation-devs` will set up a reminder for 30 minutes from the original invocation. At that time, it will notify both the original creator of the reminder and `@task-automation-devs`.
    - Example: `/deploy-reminder 15` will set up a reminder for 15 minutes from the original invocation without tagging anyone besides the original creator.
    - Example: `/deploy-reminder in 15` will also set up a reminder for 15 minutes from the original invocation.
- `/deploy-reminder at <timestamp_to_deploy> <optional-notification-recipients>`
    - Example: `/deploy-reminder at 15:30` will set up a reminder at 3:30PM Pacific.


### Deploy by release branch
- `/deploy-by-branch <circle_ci_release_branch_name>`
    - This command creates a prompt to deploy the latest commit ready to deploy for `<circle_ci_release_branch_name>`
    - Example: `/deploy-by-branch release/devex/hello_docker` will present a prompt to approve the latest job hold on the `release/devex/hello_docker` branch. If a user elects to deploy, a confirmation dialog is brought up, after which approval is submitted.


## Setup
To start, make sure the `Heroku Deploy App` is installed in your workspace in Slack.

From there, in order to get Heroku to play nice with the bot, you'll need to add `heroku-api+deploy-helper@statestitle.com` to your app's access page (i.e. https://dashboard.heroku.com/apps/<app_name>/access) with the Deploy or Operate permissions.


### Local testing
We used [ngrok](https://api.slack.com/start/building/bolt-python#ngrok) to test locally by
  - spinning up a local ngrok server,
  - setting the [slash command](https://api.slack.com/apps/A028PPZ53GD/slash-commands) request URL to the ngrok generated URL,
  - sending a command and watching the traffic route to the appropriate event handler. Note that you can use a debugger and inspect the commands as well
