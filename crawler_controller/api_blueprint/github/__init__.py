
from crawler_controller.api_blueprint import api
from flask import request

from crawler_controller.models.github import GitHubUser
from crawler_controller.models.platforms import Platform
from crawler_controller import db

@api.route('/github', methods=['GET', 'POST'])
def github_usernames():
    if request.method=='GET':
        """ return a block of usernames to crawl repos for"""

    elif request.method=='POST':
        """ add or update usernames (from user crawler)
        expects a list of results and the platform base url

        {
            'platform_base_url': 'https://api.github.com/',
            'platform_type': 'github',
            'results': [...]
        }
        """
        platform_base_url = request.json['platform_base_url']
        platform_type = request.json['platform_type']
        platform_state = request.json['state']

        platform = Platform.query.filter_by(platform_type=platform_type, base_url=platform_base_url).first()
        platform.update_state(platform_state)

        for result in request.json['results']:
            gh_user = GitHubUser.from_gh_result(platform, result)
            db.session.add(gh_user)
        db.session.commit()

    return ''

@api.route('/github/<id>/next_users', methods=['GET'])
def github_get_next_users():
    """ return a block of usernames to crawl """
    return ''


@api.route('/github/<id>/repos', methods=['POST'])
def github_repos():
    """ endpoint to post crawled repos to """
    return ''
