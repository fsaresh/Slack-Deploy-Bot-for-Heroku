from actions.deploy_branch import BranchDeployAction, BranchDeployError, DeployPromptContext
from slack_sdk import WebClient
from typing import Dict
from unittest import TestCase
from unittest.mock import MagicMock, patch
import json


mock_client = MagicMock(WebClient)
mock_circle_token = 'FAKE_TOKEN'


def generate_command_body(
        user_id: str = 'user123',
        branch_name: str = 'branchName5000',
        workflow_id: str = '1234-5678-9012',
        job_id: str = '2345-6789-0123',
        commit_sha: str = '3456-7890-1234',
        commit_subject: str = 'HDHDH-1: Initial HDHDH commit'
) -> Dict:
    value_payload = dict()
    value_payload[DeployPromptContext.BRANCH_NAME.value] = branch_name
    value_payload[DeployPromptContext.COMMIT_SHA.value] = commit_sha
    value_payload[DeployPromptContext.COMMIT_SUBJECT.value] = commit_subject
    value_payload[DeployPromptContext.JOB_ID.value] = job_id
    value_payload[DeployPromptContext.WORKFLOW_ID.value] = workflow_id

    return {
        'user': {
            'id': user_id
        },
        'channel': {
            'id': 'CBR2V3XEX',
            'name': 'deploy-bot-testing'
        },
        'message': {
            'ts': "1548261231.000200"  # Random timestamp
        },
        'actions': [{
            'value': json.dumps(value_payload)
        }]
    }


class TestDeployBranch(TestCase):
    class MockResponse:
        def __init__(self, status_code: int, content: str, json_data: Dict = None):
            self.status_code = status_code
            self.content = content.encode('utf-8')
            self.json_data = json_data

    def setUp(self) -> None:
        mock_client.reset_mock()

    @patch('requests.post', return_value=MockResponse(status_code=400, content="Bad request"))
    def test_bad_circle_ci_status(self, mock_post):
        body = generate_command_body()
        deploy_prompt = BranchDeployAction(body=body, web_client=mock_client, circle_ci_token=mock_circle_token)
        with self.assertRaises(BranchDeployError):
            deploy_prompt.deploy()
        mock_post.assert_called_once()
        mock_client.chat_update.assert_not_called()

    def test_deploy_prompt_missing_approval(self):
        body = generate_command_body()
        deploy_prompt = BranchDeployAction(body=body, web_client=mock_client, circle_ci_token=mock_circle_token)
        deploy_prompt.cancel_prompt()
        mock_client.chat_update.assert_called_once()
