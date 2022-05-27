from enum import Enum
from github.PullRequest import PullRequest
from helpers.command_helpers import PR_DATE_FORMAT
from typing import Optional, Dict
import json


class BlockKeys(str, Enum):
    ACTION_ID = 'action_id'
    CONFIRM = 'confirm'
    DENY = 'deny'
    ELEMENTS = 'elements'
    EMOJI = 'emoji'
    STYLE = 'style'
    TEXT = 'text'
    TITLE = 'title'
    TYPE = 'type'
    VALUE = 'value'


class BlockTypeStyles(str, Enum):
    ACTIONS = 'actions'
    BUTTON = 'button'
    DANGER = 'danger'
    MARKDOWN = 'mrkdwn'
    PLAIN_TEXT = 'plain_text'
    PRIMARY = 'primary'
    SECTION = 'section'


def generate_deploy_preamble_block(branch_name: str, recipient: Optional[str] = None) -> Dict:
    prompt = f'Approval requested for branch {branch_name}'
    if recipient:
        prompt += f', {recipient}'

    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: prompt
        }
    }


def generate_deploy_commit_block(commit_sha: str, commit_subject: str) -> Dict:
    prompt = f'Commit to be deployed:' \
             f'\n*SHA:* {commit_sha}' \
             f'\n*Subject:* {commit_subject}'

    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: prompt
        }
    }


def generate_divider_block() -> Dict:
    return {
        BlockKeys.TYPE: 'divider'
    }


def generate_deploy_actions_block(deploy_prompt_block_context: Dict) -> Dict:
    approve_action = {
        BlockKeys.TYPE: BlockTypeStyles.BUTTON,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
            BlockKeys.TEXT: ':white_check_mark: Approve and Deploy',
            BlockKeys.EMOJI: True
        },
        BlockKeys.CONFIRM: {
            BlockKeys.TITLE: {
                BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
                BlockKeys.TEXT: 'Are you sure?',
            },
            BlockKeys.TEXT: {
                BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
                BlockKeys.TEXT: f'Deploy `{deploy_prompt_block_context.get("branch_name")}`?',
            },
            BlockKeys.CONFIRM: {
                BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
                BlockKeys.TEXT: 'Deploy',
            },
            BlockKeys.DENY: {
                BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
                BlockKeys.TEXT: 'Stop, I changed my mind!',
            },
        },
        BlockKeys.STYLE: BlockTypeStyles.PRIMARY,
        BlockKeys.VALUE: json.dumps(deploy_prompt_block_context),
        BlockKeys.ACTION_ID: 'approve_deploy'
    }

    cancel_action = {
        BlockKeys.TYPE: BlockTypeStyles.BUTTON,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.PLAIN_TEXT,
            BlockKeys.TEXT: ":negative_squared_cross_mark: Cancel",
            BlockKeys.EMOJI: True
        },
        BlockKeys.STYLE: BlockTypeStyles.DANGER,
        BlockKeys.VALUE: json.dumps(deploy_prompt_block_context),
        BlockKeys.ACTION_ID: 'cancel_deploy_prompt'
    }

    return {
        BlockKeys.TYPE: BlockTypeStyles.ACTIONS,
        BlockKeys.ELEMENTS: [
            approve_action,
            cancel_action
        ]
    }


def generate_deploy_approved_at_timestamp_block(timestamp: str, user_id: str) -> Dict:
    timestamp_message = f'DEPLOY APPROVED ' \
                        + generate_user_interaction_timestamp(timestamp=timestamp, user_id=user_id)
    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: timestamp_message
        }
    }


def generate_deploy_cancelled_at_timestamp_block(timestamp: str, user_id: str) -> Dict:
    timestamp_message = 'Removing button to deploy after prompt cancellation ' \
                        + generate_user_interaction_timestamp(timestamp=timestamp, user_id=user_id)
    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: timestamp_message
        }
    }


def generate_user_interaction_timestamp(timestamp: str, user_id: str) -> str:
    clean_timestamp = timestamp.split('.')[0]
    return f'by <@{user_id}> at <!date^{clean_timestamp}^' \
           '{date_num} {time}|unknown datetime>'


def generate_no_commits_block(app_name: str, item_filter: str) -> Dict:
    """ Generate a Slack-friendly human-readable block to submit back via `respond` for no new merges
    """
    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: f"No commits were merged matching `{item_filter}` since `{app_name}` was last deployed"
        }
    }


def generate_pr_summary_block(pr: PullRequest) -> Dict:
    """ Generate a Slack-friendly human-readable block to submit back via `respond`
    """
    pr_merged_date = pr.merged_at.date().strftime(PR_DATE_FORMAT)
    return {
        BlockKeys.TYPE: BlockTypeStyles.SECTION,
        BlockKeys.TEXT: {
            BlockKeys.TYPE: BlockTypeStyles.MARKDOWN,
            BlockKeys.TEXT: f"• {pr_merged_date}: *{pr.title.strip()}* (<{pr.html_url}|#{pr.number}>)"
        }
    }
