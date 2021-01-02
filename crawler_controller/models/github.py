from crawler_controller import db



class GitHubUser():
    """
    {
    "login": "errfree",
    "id": 44,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjQ0",
    "avatar_url": "https://avatars2.githubusercontent.com/u/44?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/errfree",
    "html_url": "https://github.com/errfree",
    "followers_url": "https://api.github.com/users/errfree/followers",
    "following_url": "https://api.github.com/users/errfree/following{/other_user}",
    "gists_url": "https://api.github.com/users/errfree/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/errfree/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/errfree/subscriptions",
    "organizations_url": "https://api.github.com/users/errfree/orgs",
    "repos_url": "https://api.github.com/users/errfree/repos",
    "events_url": "https://api.github.com/users/errfree/events{/privacy}",
    "received_events_url": "https://api.github.com/users/errfree/received_events",
    "type": "Organization",
    "site_admin": false
    },
    """
    __tablename__ = 'github_users'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.ForeignKey('Platform'), nullable=False)

    gh_login = db.Column(db.String(128))
    gh_id = db.Column(db.Integer())
    gh_node_id = db.Column(db.String(24))
    gh_type = db.Column(db.String(12))
    gh_site_admin = db.Column(db.Boolean())

    @staticmethod
    def from_gh_result(platform, result: dict) -> 'GitHubUser':
        gh_user = GitHubUser()
        gh_user.gh_id = result['id']
        gh_user.gh_login = result['login']
        gh_user.gh_node_id = result['node_id']
        gh_user.gh_type = result['type']
        gh_user.gh_site_admin = result['site_admin']
        return gh_user

    def __repr__(self):
        return f''



class GithubRepo():
    __tablename__ = 'github_repos'
    id = db.Column(db.Integer, primary_key=True)
    user = ''
    name = ''

