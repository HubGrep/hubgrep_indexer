
mock_github_repos = [
    {
        "id": "MDEwOlJlcG9zaXRvcnkx",
        "name": "mockrepo",
        "nameWithOwner": "repomock/mockrepo",
        "homepageUrl": None,
        "url": "https://github.com/repomock/mockrepo",
        "createdAt": "2010-03-09T05:10:10Z",
        "updatedAt": "2010-03-09T16:57:19Z",
        "pushedAt": "2010-03-09T16:57:19Z",
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
            "login": "repomock",
            "id": "MDQ6VXNlcjA=",
            "url": "https://github.com/repomock"
        },
        "repositoryTopics": {
            "nodes": []
        },
        "primaryLanguage": {
            "name": "Python"
        },
        "licenseInfo": {
            "name": "GNU General Public License v2.0",
            "nickname": "GNU GPLv2"
        }
    },
    {
        "id": "MDEwOlJlcG9zaXRvcnky",
        "name": "mockrepo2",
        "nameWithOwner": "repomock2/mockrepo2",
        "homepageUrl": None,
        "url": "https://github.com/repomock/mockrepo2",
        "createdAt": "2010-03-09T05:10:10Z",
        "updatedAt": "2010-03-09T16:57:19Z",
        "pushedAt": "2010-03-09T16:57:19Z",
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
            "login": "repomock2",
            "id": "MDQ6VXNlcjE=",
            "url": "https://github.com/repomock2"
        },
        "repositoryTopics": {
            "nodes": []
        },
        "primaryLanguage": {
            "name": "Python"
        },
        "licenseInfo": {
            "name": "GNU General Public License v2.0",
            "nickname": "GNU GPLv2"
        }
    }
]

mock_gitea_repos = [
    {
        'id': 1,
        'owner': {'id': 1,
                  'login': 'user.1',
                  'full_name': '',
                  'email': '',
                  'avatar_url': 'http://gitea',
                  'username': 'user.1'},
        'name': 'repo-name1',
        'full_name': 'user.1/repo-name1',
        'description': '',
        'empty': False,
        'private': False,
        'fork': False,
        'parent': None,
        'mirror': False,
        'size': 5188,
        'html_url': 'http://gitea',
        'ssh_url': 'root@gitea.git',
        'clone_url': 'http://gitea.git',
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
                        'pull': True}
    },
    {
        'id': 2,
        'owner': {'id': 2,
                  'login': 'user.2',
                  'full_name': '',
                  'email': '',
                  'avatar_url': 'http://gitea',
                  'username': 'user.2'},
        'name': 'repo-name2',
        'full_name': 'user.2/repo-name2',
        'description': '',
        'empty': False,
        'private': False,
        'fork': False,
        'parent': None,
        'mirror': False,
        'size': 5188,
        'html_url': 'http://gitea',
        'ssh_url': 'root@gitea.git',
        'clone_url': 'http://gitea.git',
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
                        'pull': True}
    }
]

mock_gitlab_repos = [
    {
        'id': 1,
        'description': 'test1',
        'name': 'testrepo1',
        'name_with_namespace': 'test user1 / testrepo1',
        'path': 'testrepo1',
        'path_with_namespace': 'testpath1/testrepo1',
        'created_at': '2016-05-30T04:27:14.463Z',
        'default_branch': 'master',
        'tag_list': [],
        'topics': ["key-maybe-not-here"],
        'ssh_url_to_repo': 'git@gitlab.git',
        'http_url_to_repo': 'https://gitlab.git',
        'web_url': 'https://gitlab.com',
        'readme_url': 'https://gitlab.com/README.md',
        'avatar_url': None,
        'forks_count': 0,
        'star_count': 0,
        'last_activity_at': '2016-05-30T04:27:15.194Z',
        'namespace': {'id': 502506,
                      'name': 'test user1',
                      'path': 'testpath1',
                      'kind': 'user',
                      'full_path': 'testpath1',
                      'parent_id': None,
                      'avatar_url': 'https://secure.gravatar.com/avatar/',
                      'web_url': 'https://gitlab.com/testpath1'}
    },
    {
        'id': 2,
        'description': 'test2',
        'name': 'testrepo2',
        'name_with_namespace': 'test user2 / testrepo2',
        'path': 'testrepo2',
        'path_with_namespace': 'testpath2/testrepo2',
        'created_at': '2016-05-30T04:27:14.463Z',
        'default_branch': 'master',
        'tag_list': [],
        'topics': ["key-maybe-not-here"],
        'ssh_url_to_repo': 'git@gitlab.git',
        'http_url_to_repo': 'https://gitlab.git',
        'web_url': 'https://gitlab.com',
        'readme_url': 'https://gitlab.com/README.md',
        'avatar_url': None,
        'forks_count': 0,
        'star_count': 0,
        'last_activity_at': '2016-05-30T04:27:15.194Z',
        'namespace': {'id': 502506,
                      'name': 'test user2',
                      'path': 'testpath2',
                      'kind': 'user',
                      'full_path': 'testpath2',
                      'parent_id': None,
                      'avatar_url': 'https://secure.gravatar.com/avatar/',
                      'web_url': 'https://gitlab.com/testpath2'}
    }
]
