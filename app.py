from slack_bolt import App
from slack_sdk import WebClient
import os
import logging

from actions.deploy_branch import BranchDeployAction, BranchDeployError
from commands.commit_list import CommitList, get_commit_list_help_message
from commands.deploy_prompt import PromptBranchDeploy, get_deploy_by_branch_help_message, PromptBranchDeployError
from commands.deploy_reminder import DeployReminder, get_deploy_reminder_help_message, DeployReminderError
from commands.latest_deploy import LatestDeploy
from helpers.command_helpers import CIRCLE_CI_TOKEN

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initializes app with bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    LOG.info(f'Say message for {say}')
    say(f"Hey there <@{message['user']}>!")


@app.command("/commit-list")
@app.command("/commit-list-test")
def commit_list(ack, command, respond):
    ack()
    try:
        CommitList(command=command, respond=respond).get_commit_list()
    except Exception as e:
        respond(get_commit_list_help_message(command=command, exception=e))
        LOG.error(e)


@app.command("/latest-deploy")
def latest_deploy(ack, command, respond):
    ack()
    try:
        LatestDeploy(command=command, respond=respond).get_latest_deployed_commit()
    except Exception as e:
        respond(f'Unable to get commits: {e}')


@app.command("/deploy-reminder")
@app.command("/deploy-reminder-test")
def deploy_reminder(ack, command, say):
    ack()
    try:
        DeployReminder(say=say, command=command, web_client=client).schedule_reminder()
    except DeployReminderError as e:
        say(get_deploy_reminder_help_message(command=command, exception=e))
        LOG.error(e)


@app.command("/deploy-by-branch")
@app.command("/deploy-by-branch-test")
def prompt_deploy_by_branch(ack, command, say):
    ack()
    try:
        PromptBranchDeploy(
            command=command,
            web_client=client,
            circle_ci_token=CIRCLE_CI_TOKEN
        ).prompt_deploy()
    except PromptBranchDeployError as e:
        say(get_deploy_by_branch_help_message(command=command, exception=e))
        LOG.error(e)


@app.action("approve_deploy")
def deploy_by_branch(ack, body, say):
    ack()
    try:
        BranchDeployAction(
            body=body,
            web_client=client,
            circle_ci_token=CIRCLE_CI_TOKEN
        ).deploy()
    except BranchDeployError as e:
        say(f'Unable to deploy: {e}')
        LOG.error(e)


@app.action("cancel_deploy_prompt")
def deploy_by_branch(ack, body, say):
    ack()
    try:
        BranchDeployAction(
            body=body,
            web_client=client,
            circle_ci_token=CIRCLE_CI_TOKEN
        ).cancel_prompt()
    except BranchDeployError as e:
        say(f'Unable to remove approval button: {e}')
        LOG.error(e)


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
