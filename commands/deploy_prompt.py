from actions.deploy_branch import DeployPromptContext
from helpers.blocks import (
    generate_deploy_actions_block, generate_divider_block,
    generate_deploy_preamble_block, generate_deploy_commit_block
)
from helpers.command_helpers import SlackHerokuDeployError, parse_argument, BASE_CIRCLE_CI_API_URL
from http import HTTPStatus
from slack_sdk import WebClient
from typing import Tuple, Optional, Dict
import json
import logging
import requests

LOG = logging.getLogger(__name__)

PIPELINE_URL_SUFFIX = 'project/gh/StatesTitle/underwriter/pipeline?branch='
APPROVAL_JOB = 'approval'


class PromptBranchDeployError(SlackHerokuDeployError):
    pass


def get_request_items(response: requests.Response, key: str, from_type: str, to_type: str):
    if response.status_code != HTTPStatus.OK:
        raise PromptBranchDeployError(f'Bad status received from CircleCI: {response.status_code} '
                                      f'for {from_type} {key}:\n {response.content.decode("utf-8")}')

    values = response.json().get('items')
    if not values:
        raise PromptBranchDeployError(f'No {to_type} found for {from_type}: {key}')
    return values


class PromptBranchDeploy:
    """ Usage: /deploy-by-branch release/fee_collab

    """
    def __init__(self, command: Dict, web_client: WebClient, circle_ci_token: str):
        self.command = command
        self.web_client = web_client
        self.circle_headers = {'Circle-Token': circle_ci_token}

        self.branch_name = parse_argument(self.command['text'], arg_index=0)
        self.tag_recipient = parse_argument(self.command['text'], arg_index=1)

    def prompt_deploy(self):
        if not self.branch_name:
            raise PromptBranchDeployError(f"Unable to deploy: no branch name specified in {self.command['text']}")

        pipeline_id, commit_subject, commit_sha = self.get_pipeline_id_by_branch_name()
        workflow_id = self.get_workflow_id_by_pipeline_id(pipeline_id)
        job_id = self.get_approval_job_id_by_workflow_id(workflow_id)
        if not job_id:
            raise PromptBranchDeployError(f'No approval job_id found for pipeline_id {pipeline_id} '
                                          f'and workflow_id {workflow_id}')

        blocks = json.dumps(self.generate_deploy_prompt_message(
            commit_subject=commit_subject, commit_sha=commit_sha, workflow_id=workflow_id, job_id=job_id
        ))
        self.web_client.chat_postMessage(channel=self.command['channel_id'], blocks=blocks)

    def get_pipeline_id_by_branch_name(self) -> Tuple[str, str, str]:
        # https://circleci.com/docs/api/v2/#operation/listPipelinesForProject
        response = requests.get(BASE_CIRCLE_CI_API_URL + PIPELINE_URL_SUFFIX + self.branch_name,
                                headers=self.circle_headers)
        pipelines = get_request_items(response=response, key=self.branch_name,
                                      from_type='branch name', to_type='pipeline')
        pipeline, *_ = pipelines
        LOG.info(f'Branch {self.branch_name} has most recent pipeline: {pipeline}')
        return pipeline.get('id'), pipeline['vcs']['commit']['subject'], pipeline['vcs']['revision']

    def get_workflow_id_by_pipeline_id(self, pipeline_id: str) -> str:
        # https://circleci.com/docs/api/v2/#operation/listWorkflowsByPipelineId
        response = requests.get(BASE_CIRCLE_CI_API_URL + 'pipeline/' + pipeline_id + '/workflow',
                                headers=self.circle_headers)
        workflows = get_request_items(response=response, key=pipeline_id,
                                      from_type='pipeline', to_type='workflow')
        workflow, *_ = workflows
        LOG.info(f'Pipeline {pipeline_id} has most recent workflow: {workflow}')
        return workflow.get('id')

    def get_approval_job_id_by_workflow_id(self, workflow_id: str) -> Optional[str]:
        # https://circleci.com/docs/api/v2/#operation/listWorkflowJobs
        response = requests.get(BASE_CIRCLE_CI_API_URL + 'workflow/' + workflow_id + '/job',
                                headers=self.circle_headers)
        jobs = get_request_items(response=response, key=workflow_id,
                                 from_type='workflow', to_type='job')
        approvals = [job for job in jobs if job['type'] == APPROVAL_JOB]
        if not approvals:
            return None

        *_, final_approval = approvals
        LOG.info(f'Workflow {workflow_id} found approval job {final_approval}')
        return final_approval.get('id')

    def generate_deploy_prompt_message(self, commit_subject: str, commit_sha: str, workflow_id: str, job_id: str):
        section_block = generate_deploy_preamble_block(recipient=self.tag_recipient, branch_name=self.branch_name)
        commit_block = generate_deploy_commit_block(commit_sha=commit_sha, commit_subject=commit_subject)
        divider_block = generate_divider_block()

        action_block_context = dict()
        action_block_context[DeployPromptContext.BRANCH_NAME.value] = self.branch_name
        action_block_context[DeployPromptContext.COMMIT_SHA.value] = commit_sha
        action_block_context[DeployPromptContext.COMMIT_SUBJECT.value] = commit_subject
        action_block_context[DeployPromptContext.JOB_ID.value] = job_id
        action_block_context[DeployPromptContext.WORKFLOW_ID.value] = workflow_id
        actions_block = generate_deploy_actions_block(action_block_context)

        all_blocks = [
            section_block,
            commit_block,
            divider_block,
            actions_block
        ]
        return all_blocks


def get_deploy_by_branch_help_message(command: Dict, exception: Exception):
    return f"Unable to deploy with parameters: `{command['text']}`, example usages:\n"\
           f"`/deploy-by-branch release/fee_collab`\n"\
           f"`/deploy-by-branch release/fee_collab @task-automation-devs`\n"\
           f"Error: {exception}"
