from enum import Enum
from http import HTTPStatus
from github.Repository import Repository
from requests import HTTPError
from typing import Optional
import logging
import os
import requests

LOG = logging.getLogger(__name__)

PR_DATE_FORMAT = '%m/%d'
HUMAN_TIMESTAMP_FORMAT = '%H:%M'
CIRCLE_CI_TOKEN = os.environ.get('CIRCLE_CI_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
HEROKU_TOKEN = os.environ.get('HEROKU_TOKEN')  # populate using heroku login; heroku auth:token
BASE_CIRCLE_CI_API_URL = 'https://circleci.com/api/v2/'


# Generic exception for SlackHerokuDeployerBot
class SlackHerokuDeployError(Exception):
    pass


class ResponseType(str, Enum):
    IN_CHANNEL = 'in_channel'
    EPHEMERAL = 'ephemeral'


def parse_argument(command_text: str, arg_index: int) -> Optional[str]:
    """ Split a command's text by spaces and grab the arg_index element if possible, else None
    """
    if not command_text:
        return None

    arguments = command_text.split(' ')
    if len(arguments) <= arg_index:
        return None
    return arguments[arg_index]


def get_heroku_git_hash(app_name: Optional[str]):
    """ Get the latest commit deployed to Heroku by inspecting the config variables
    GIT_HASH (docker apps) or the HEROKU_SLUG_COMMIT (legacy apps) set by CircleCI
    """
    url = f'https://api.heroku.com/apps/{app_name}/config-vars'
    headers = {'Accept': 'application/vnd.heroku+json; version=3', 'Authorization': f'Bearer {HEROKU_TOKEN}'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != HTTPStatus.OK:
            raise HTTPError(response.status_code)

        heroku_config_vars = response.json()

        git_hash = heroku_config_vars.get('GIT_HASH')
        if not git_hash:
            git_hash = heroku_config_vars.get('HEROKU_SLUG_COMMIT')
        return git_hash
    except HTTPError as e:
        LOG.error(f'Unable to get latest git hash from Heroku: {e}')
        return None


def get_commit_pull_pr_by_hash(repo: Repository, commit_hash: str):
    return repo.get_commit(commit_hash).get_pulls()
