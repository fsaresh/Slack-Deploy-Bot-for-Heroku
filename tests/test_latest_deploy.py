from github import Github
from github.Repository import Repository
from slack_bolt import Respond
from unittest import TestCase
from unittest.mock import MagicMock, patch

from commands.latest_deploy import LatestDeploy

mock_respond = MagicMock(Respond)


def generate_command_text(app_name: str):
    return {
        'text': f'{app_name}',
        'user_id': None,
        'channel_id': None,
    }


class TestLatestDeploy(TestCase):
    def setUp(self):
        mock_respond.reset_mock()

    @patch.object(LatestDeploy, 'get_latest_deployed_hash')
    @patch.object(Github, 'get_repo')
    @patch.object(Repository, 'get_commit')
    def test_latest_deploy(self, mock_get_commit, mock_get_repo, mock_get_git_hash):
        command = generate_command_text('hello_docker')
        latest_deploy = LatestDeploy(command=command, respond=mock_respond)
        latest_deploy.get_latest_deployed_commit()

        mock_get_git_hash.assert_called_once()
        mock_get_repo.assert_called_once()
        mock_respond.assert_called_once()
