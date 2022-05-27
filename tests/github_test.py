from github import Github
import os

ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')
OLD_COMMIT_HASH = 'd4afaa7cbf5af49f991dd94714f6a30adac074aa'
NEW_COMMIT_HASH = '873414d1782bf7553f32eafb46b308c0e8849caa'

g = Github(ACCESS_TOKEN)

repo = g.get_repo('StatesTitle/underwriter')

repo.get_commit(NEW_COMMIT_HASH).get_pulls()[0].title
# comparison = repo.compare(OLD_COMMIT_HASH, NEW_COMMIT_HASH)
# diff_commits = comparison.commits
# for commit in reversed(diff_commits):
#     print(commit.get_pulls()[0].title)


