from hubgrep_indexer.models.repositories.github import GithubRepository
from hubgrep_indexer import db

github_results = [
    {
        "id": "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==",
        # "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==" => b'010:Repository17558226'
        "name": "service.subtitles.thelastfantasy",
        "nameWithOwner": "taxigps/service.subtitles.thelastfantasy",
        "homepageUrl": None,
        "url": "https://github.com/taxigps/service.subtitles.thelastfantasy",
        "createdAt": "2014-03-09T05:10:10Z",
        "updatedAt": "2014-03-09T16:57:19Z",
        "pushedAt": "2014-03-09T16:57:19Z",
        "shortDescriptionHTML": "",
        "description": None,
        "isArchived": False,
        "isPrivate": False,
        "isFork": False,
        "isEmpty": False,
        "isDisabled": False,
        "isLocked": False,
        "isTemplate": False,
        "stargazerCount": 0,
        "forkCount": 0,
        "diskUsage": 192,
        "owner": {
            "login": "taxigps",
            "id": "MDQ6VXNlcjEwMjQzNA==",
            "url": "https://github.com/taxigps",
        },
        "repositoryTopics": {"nodes": []},
        "primaryLanguage": {"name": "Python"},
        "licenseInfo": {
            "name": "GNU General Public License v2.0",
            "nickname": "GNU GPLv2",
        },
    }
]


class TestGithubRepository:
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            repo = GithubRepository.from_dict(hosting_service.id, github_results[0])
            db.session.add(repo)
            db.session.commit()

            assert GithubRepository.query.count() == 1
            assert repo.github_id == 17558226

    def test_clean_string(self):
        assert GithubRepository.clean_string("\x00test") == "\uFFFDtest"
        assert GithubRepository.clean_string(None) == None
        assert GithubRepository.clean_string("test") == "test"
