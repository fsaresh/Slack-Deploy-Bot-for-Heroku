from github import Github
from github.Repository import Repository
from helpers.blocks import generate_no_commits_block, generate_pr_summary_block
from helpers.command_helpers import (
    parse_argument, GITHUB_TOKEN, get_heroku_git_hash,
    ResponseType, SlackHerokuDeployError
)
from slack_bolt import Respond
from typing import List, Dict
import logging
import os

LOG = logging.getLogger(__name__)


class CommitListError(SlackHerokuDeployError):
    pass


class CommitList:
    def __init__(self, respond: Respond, command: Dict):
        self.respond = respond
        self.command = command
        self.app_name = parse_argument(command_text=self.command['text'], arg_index=0)
        self.item_filter = parse_argument(command_text=self.command['text'], arg_index=1)

    def get_commit_list(self) -> List[Dict]:
        """ Get a list of commits that have been merged into `stable`
        since the last time app_name (first parameter) that touched any files
        listed in the specified item_filter (second parameter)
        """
        if not self.app_name or not self.item_filter:
            raise CommitListError(f'Missing app_name or item_filter in command text')

        self.respond(f'`{self.app_name}`: loading latest undeployed commits with item_filter `{self.item_filter}`...',
                     response_type=ResponseType.IN_CHANNEL)

        repo = Github(GITHUB_TOKEN).get_repo('StatesTitle/underwriter')
        latest_stable_commit = repo.get_branch('stable').commit
        LOG.info(f'Got latest stable commit {latest_stable_commit}')

        heroku_git_hash = self.get_deployed_git_hash()
        filtered_commits = self.get_commits_matching_filter(
            repo=repo,
            heroku_git_hash=heroku_git_hash,
            latest_stable_commit=latest_stable_commit.sha,
        )
        self.respond(blocks=filtered_commits, response_type=ResponseType.IN_CHANNEL)
        return filtered_commits

    def get_commits_matching_filter(self,
                                    repo: Repository,
                                    heroku_git_hash: str,
                                    latest_stable_commit: str) -> List[Dict]:
        results = []
        try:
            comparison = repo.compare(base=heroku_git_hash, head=latest_stable_commit)
        except Exception as e:
            LOG.error(f'Unable to compare hashes: {e}')
            self.respond('Unable to retrieve commits. See logs for details', response_type=ResponseType.IN_CHANNEL)
            return []

        for commit in comparison.commits:
            LOG.info(f'Found commit in comparison: {commit}')
            # For each commit, check and see if it affected files in the specified directory
            valid_files = any(file for file in commit.files if self.item_filter in file.filename)
            if not valid_files:
                LOG.debug(f'No files matching `{self.item_filter}` found in {commit}')
                continue

            # For relevant commits, generate the summary block in a human readable fashion
            for pr in commit.get_pulls():
                LOG.debug(f'Adding {pr} to summary')
                results.append(generate_pr_summary_block(pr))

        if not results:
            results = [generate_no_commits_block(app_name=self.app_name, item_filter=self.item_filter)]
        return results

    def get_deployed_git_hash(self):
        sample_heroku_git_hash = os.environ.get('SAMPLE_HEROKU_GIT_HASH')
        if sample_heroku_git_hash:
            LOG.info(f'Sample heroku git hash {sample_heroku_git_hash}')
            return sample_heroku_git_hash

        return get_heroku_git_hash(self.app_name)


def get_commit_list_help_message(command: Dict, exception: Exception) -> str:
    return f"Unable to get latest commits with parameters: `{command['text']}`, example usages:\n"\
           f"`/commit-list stp-instant-cd fee_collab`\n"\
           f"`/commit-list stp-resware-api-plus resware`\n"\
           f"Error: {exception}"
