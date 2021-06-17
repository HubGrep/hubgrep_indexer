from hubgrep_indexer.models.repositories.gitea import GiteaRepository
from hubgrep_indexer import db

gitea_results = [
    {
        "id": 2,
        "owner": {
            "id": 5,
            "login": "codi.cooperatiu",
            "full_name": "",
            "email": "",
            "avatar_url": "http://gitea.codi.coop/avatars/a89a876bb0456b115c77dbee684d409b",
            "username": "codi.cooperatiu",
        },
        "name": "codi-theme",
        "full_name": "codi.cooperatiu/codi-theme",
        "description": "",
        "empty": False,
        "private": False,
        "fork": False,
        "parent": None,
        "mirror": False,
        "size": 5188,
        "html_url": "http://gitea.codi.coop/codi.cooperatiu/codi-theme",
        "ssh_url": "root@gitea.codi.coop:codi.cooperatiu/codi-theme.git",
        "clone_url": "http://gitea.codi.coop/codi.cooperatiu/codi-theme.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 3,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-01-25T18:52:35Z",
        "updated_at": "2019-05-20T18:55:46Z",
        "permissions": {"admin": False, "push": False, "pull": True},
    }
]


class TestGiteaRepository:
    def test_add_from_dict(self, test_app, test_client, hosting_service):
        with test_app.app_context():
            repo = GiteaRepository.from_dict(hosting_service.id, gitea_results[0])
            db.session.add(repo)
            db.session.commit()

            assert GiteaRepository.query.count() == 1
            assert repo.gitea_id == 2