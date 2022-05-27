from commands.deploy_prompt import PromptBranchDeploy, PromptBranchDeployError
from slack_bolt import Respond
from slack_sdk import WebClient
from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock, patch


mock_respond = MagicMock(Respond)
mock_client = MagicMock(WebClient)
mock_circle_token = 'FAKE_TOKEN'


def generate_command_text(branch_name: str, recipient: Optional[str] = None):
    return {
        'text': f'{branch_name} {recipient}',
        'user_id': None,
        'channel_id': None,
    }


class TestDeployPrompt(TestCase):
    def setUp(self) -> None:
        mock_respond.reset_mock()
        mock_client.reset_mock()

    def test_missing_branch_name(self):
        command = generate_command_text(branch_name='')
        deploy_prompt = PromptBranchDeploy(command=command, web_client=mock_client, circle_ci_token=mock_circle_token)
        with self.assertRaises(PromptBranchDeployError):
            deploy_prompt.prompt_deploy()

    @patch.object(PromptBranchDeploy, 'get_pipeline_id_by_branch_name', return_value=('1234-5678-9012', 'commit subject', 'sha'))
    @patch.object(PromptBranchDeploy, 'get_workflow_id_by_pipeline_id', return_value='2345-6789-0123')
    @patch.object(PromptBranchDeploy, 'get_approval_job_id_by_workflow_id', return_value=None)
    def test_deploy_prompt_missing_approval(self, mock_get_job, mock_get_workflow, mock_get_pipeline):
        command = generate_command_text(branch_name='release/test-deploy')
        deploy_prompt = PromptBranchDeploy(command=command, web_client=mock_client, circle_ci_token=mock_circle_token)
        with self.assertRaises(PromptBranchDeployError):
            deploy_prompt.prompt_deploy()
        mock_get_job.assert_called_once()
        mock_get_workflow.assert_called_once()
        mock_get_pipeline.assert_called_once()
        mock_client.chat_postMessage.assert_not_called()

    @patch.object(PromptBranchDeploy, 'get_pipeline_id_by_branch_name', return_value=('1234-5678-9012', 'commit subject', 'sha'))
    @patch.object(PromptBranchDeploy, 'get_workflow_id_by_pipeline_id', return_value='2345-6789-0123')
    @patch.object(PromptBranchDeploy, 'get_approval_job_id_by_workflow_id', return_value='34567')
    def test_deploy_prompt_mocked(self, mock_get_job, mock_get_workflow, mock_get_pipeline):
        command = generate_command_text(branch_name='release/test-deploy')
        deploy_prompt = PromptBranchDeploy(command=command, web_client=mock_client, circle_ci_token=mock_circle_token)
        deploy_prompt.prompt_deploy()
        mock_get_job.assert_called_once()
        mock_get_workflow.assert_called_once()
        mock_get_pipeline.assert_called_once()
        mock_client.chat_postMessage.assert_called_once()
