from enum import Enum

from helpers.blocks import generate_deploy_preamble_block, generate_divider_block, \
    generate_deploy_approved_at_timestamp_block, generate_deploy_cancelled_at_timestamp_block, \
    generate_deploy_commit_block
from helpers.command_helpers import BASE_CIRCLE_CI_API_URL, parse_argument, SlackHerokuDeployError
from http import HTTPStatus
from slack_sdk import WebClient
from typing import Dict
import json
import logging
import requests

LOG = logging.getLogger(__name__)


class DeployPromptContext(Enum):
    BRANCH_NAME = 'branch_name'
    COMMIT_SHA = 'commit_sha'
    COMMIT_SUBJECT = 'commit_subject'
    JOB_ID = 'job_id'
    WORKFLOW_ID = 'workflow_id'


class BranchDeployError(SlackHerokuDeployError):
    pass


class BranchDeployAction:
    def __init__(self, body: Dict, web_client: WebClient, circle_ci_token: str):
        self.body = body
        self.web_client = web_client
        self.circle_headers = {'Circle-Token': circle_ci_token}

        self.action = self.get_action_from_body()
        self.user_id = self.body['user']['id']

        LOG.info(f'Action entry: {self.action}')
        block_context = json.loads(self.action['value'])
        self.branch_name = block_context[DeployPromptContext.BRANCH_NAME.value]
        self.commit_sha = block_context[DeployPromptContext.COMMIT_SHA.value]
        self.commit_subject = block_context[DeployPromptContext.COMMIT_SUBJECT.value]
        self.job_id = block_context[DeployPromptContext.JOB_ID.value]
        self.workflow_id = block_context[DeployPromptContext.WORKFLOW_ID.value]

    def deploy(self) -> None:
        # https://circleci.com/docs/api/v2/#operation/approvePendingApprovalJobById
        response = requests.post(BASE_CIRCLE_CI_API_URL + 'workflow/' + self.workflow_id + '/approve/' + self.job_id,
                                 headers=self.circle_headers)
        if response.status_code != HTTPStatus.ACCEPTED:
            raise BranchDeployError(f'Bad status received from CircleCI: {response.status_code} '
                                    f'for approving job {self.job_id}:\n {response.content.decode("utf-8")}')

        LOG.info(f'Got status {response.status_code} for job approval, info: {response.content.decode("utf-8")}')
        timestamp = self.body['message']['ts']
        blocks = self.generate_deploy_approved_at_timestamp_message(timestamp=timestamp)
        self.web_client.chat_update(channel=self.body['channel']['id'], ts=timestamp, blocks=blocks)

    def cancel_prompt(self):
        timestamp = self.body['message']['ts']
        blocks = self.generate_deploy_canceled_at_timestamp_message(timestamp=timestamp)
        self.web_client.chat_update(channel=self.body['channel']['id'], ts=timestamp, blocks=blocks)

    def get_action_from_body(self):
        action, *_ = self.body['actions']
        if not action:
            raise BranchDeployError(f'No action value in place')
        return action

    def generate_deploy_approved_at_timestamp_message(self, timestamp: str):
        section_block = generate_deploy_preamble_block(branch_name=self.branch_name)
        commit_block = generate_deploy_commit_block(commit_sha=self.commit_sha, commit_subject=self.commit_subject)
        divider_block = generate_divider_block()
        timestamp_approved_block = generate_deploy_approved_at_timestamp_block(timestamp=timestamp,
                                                                               user_id=self.user_id)

        all_blocks = [
            section_block,
            commit_block,
            divider_block,
            timestamp_approved_block,
        ]
        return all_blocks

    def generate_deploy_canceled_at_timestamp_message(self, timestamp: str):
        section_block = generate_deploy_preamble_block(branch_name=self.branch_name)
        commit_block = generate_deploy_commit_block(commit_sha=self.commit_sha, commit_subject=self.commit_subject)
        divider_block = generate_divider_block()
        timestamp_cancelled_block = generate_deploy_cancelled_at_timestamp_block(timestamp=timestamp,
                                                                                 user_id=self.user_id)
        all_blocks = [
            section_block,
            commit_block,
            divider_block,
            timestamp_cancelled_block,
        ]
        return all_blocks
