from github import Github
from helpers.command_helpers import parse_argument, get_heroku_git_hash, GITHUB_TOKEN, get_commit_pull_pr_by_hash, \
    ResponseType
from helpers.blocks import generate_pr_summary_block
from slack_bolt import Respond
from typing import Dict
import logging

LOG = logging.getLogger(__name__)


class LatestDeploy:
    def __init__(self, respond: Respond, command: Dict):
        self.command = command
        self.respond = respond
        self.app_name = parse_argument(command_text=self.command['text'], arg_index=0)

    def get_latest_deployed_commit(self):
        latest_git_hash = self.get_latest_deployed_hash()
        repo = Github(GITHUB_TOKEN).get_repo('StatesTitle/underwriter')
        commit_prs = get_commit_pull_pr_by_hash(repo, latest_git_hash)

        self.respond(f'Latest Deployed on {self.app_name}:', response_type=ResponseType.IN_CHANNEL)
        for pr in commit_prs:
            self.respond(blocks=[generate_pr_summary_block(pr)], response_type=ResponseType.IN_CHANNEL)

    def get_latest_deployed_hash(self):
        LOG.info(f'Getting latest deployed hash for {self.app_name}')
        latest_git_hash = get_heroku_git_hash(self.app_name)
        LOG.info(f'Latest git hash found: {latest_git_hash}')
        return latest_git_hash
