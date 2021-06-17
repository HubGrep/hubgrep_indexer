from iso8601 import iso8601

from hubgrep_indexer import db

"""
    {'id': 2,
    'owner': {'id': 5,
              'login': 'codi.cooperatiu',
              'full_name': '',
              'email': '',
              'avatar_url': 'http://gitea.codi.coop/avatars/a89a876bb0456b115c77dbee684d409b',
              'username': 'codi.cooperatiu'},
    'name': 'codi-theme',
    'full_name': 'codi.cooperatiu/codi-theme',
    'description': '',
    'empty': False,
    'private': False,
    'fork': False,
    'parent': None,
    'mirror': False,
    'size': 5188,
    'html_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme',
    'ssh_url': 'root@gitea.codi.coop:codi.cooperatiu/codi-theme.git',
    'clone_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme.git',
    'website': '',
    'stars_count': 0,
    'forks_count': 0,
    'watchers_count': 3,
    'open_issues_count': 0,
    'default_branch': 'master',
    'created_at': '2018-01-25T18:52:35Z',
    'updated_at': '2019-05-20T18:55:46Z',
    'permissions': {'admin': False,
                    'push': False,
                    'pull': True}}
    """


class GiteaRepository(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    hosting_service_id = db.Column(
        db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
    )
    hosting_service = db.relationship("HostingService")

    gitea_id = db.Column(db.Integer)  # 2
    name = db.Column(db.String(200))  # "repo_name",
    owner_username = db.Column(db.String(200))  # "owner {username: username}",
    description = db.Column(db.Text)  # "repo description",
    empty = db.Column(db.Boolean)  # "False",
    private = db.Column(db.Boolean)  # "False",
    fork = db.Column(db.Boolean)  # "False",
    # parent = db.Column(db.Boolean)  # "None",
    mirror = db.Column(db.Boolean)  # "False",
    size = db.Column(db.Integer)  # "repo_name",
    website = db.Column(db.String(200))  # "repo_name",
    stars_count = db.Column(db.Integer)  # "repo_name",
    forks_count = db.Column(db.String(200))  # "repo_name",
    watchers_count = db.Column(db.Integer)  # "repo_name",
    open_issues_count = db.Column(db.Integer)  # "repo_name",
    default_branch = db.Column(db.String(200))  # "repo_name",
    created_at = db.Column(db.DateTime)  # "createdAt": "2014-03-09T05:10:10Z",
    updated_at = db.Column(db.DateTime)  # "updatedAt": "2014-03-09T16:57:19Z",
    pushed_at = db.Column(db.DateTime)  # "pushedAt": "2014-03-09T16:57:19Z",

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True):
        owner_username = d["owner"]["username"]
        name = d["name"]

        repo = cls.query.filter_by(
            hosting_service_id=hosting_service_id,
            owner_username=owner_username,
            name=name,
        ).first()
        if not update and not repo:
            raise Exception("repo not found!")
        if not repo:
            repo = cls()

        repo.hosting_service_id = hosting_service_id
        repo.gitea_id = d["id"]
        repo.name = name
        repo.owner_username = owner_username
        repo.description = d["description"]
        repo.empty = d["empty"]
        repo.private = d["private"]
        repo.fork = d["fork"]
        repo.mirror = d["mirror"]
        repo.size = d["size"]
        repo.website = d["website"]
        repo.stars_count = d["stars_count"]
        repo.forks_count = d["forks_count"]
        repo.watchers_count = d["watchers_count"]
        repo.open_issues_count = d["open_issues_count"]
        repo.default_branch = d["default_branch"]
        repo.created_at = iso8601.parse_date(d["created_at"])
        repo.updated_at = iso8601.parse_date(d["updated_at"])

        return repo