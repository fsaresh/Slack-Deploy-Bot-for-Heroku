from commands.commit_list import CommitList, CommitListError
from github import Github
from github.Repository import Repository
from slack_bolt import Respond
from unittest import TestCase
from unittest.mock import MagicMock, patch

mock_respond = MagicMock(Respond)


def generate_command_text(app_name: str, item_filter: str):
    return {
        'text': f'{app_name} {item_filter}',
        'user_id': None,
        'channel_id': None,
    }


class TestCommitList(TestCase):
    def setUp(self):
        mock_respond.reset_mock()

    @patch.object(CommitList, 'get_deployed_git_hash')
    @patch.object(Github, 'get_repo')
    @patch.object(Repository, 'get_branch')
    def test_get_commit_list(self, mock_get_branch, mock_get_repo, mock_get_git_hash):
        command = generate_command_text(app_name='hello_docker', item_filter='devex')
        latest_deploy = CommitList(command=command, respond=mock_respond)
        latest_deploy.get_commit_list()

        mock_get_git_hash.assert_called_once()
        mock_get_repo.assert_called_once()
        self.assertEqual(2, mock_respond.call_count)

    @patch.object(CommitList, 'get_deployed_git_hash')
    @patch.object(Github, 'get_repo')
    @patch.object(Repository, 'get_branch')
    def test_get_commit_list_missing_app_name(self, mock_get_branch, mock_get_repo, mock_get_git_hash):
        command = generate_command_text(app_name='', item_filter='item_filter')
        latest_deploy = CommitList(command=command, respond=mock_respond)
        with self.assertRaises(CommitListError):
            latest_deploy.get_commit_list()

        mock_get_git_hash.assert_not_called()
        mock_get_repo.assert_not_called()
        mock_respond.assert_not_called()

    @patch.object(CommitList, 'get_deployed_git_hash')
    @patch.object(Github, 'get_repo')
    @patch.object(Repository, 'get_branch')
    def test_get_commit_list_missing_item_filter(self, mock_get_branch, mock_get_repo, mock_get_git_hash):
        command = generate_command_text(app_name='app_name', item_filter='')
        latest_deploy = CommitList(command=command, respond=mock_respond)
        with self.assertRaises(CommitListError):
            latest_deploy.get_commit_list()

        mock_get_git_hash.assert_not_called()
        mock_get_repo.assert_not_called()
        mock_respond.assert_not_called()
