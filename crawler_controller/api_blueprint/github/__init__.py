from crawler_controller.api_blueprint import api
from flask import request


@api.route('/github', methods=['GET'])
def github_get():
    """ get a list of github servers """
    return ''


@api.route('/github/<id>', methods=['GET', 'POST'])
def github_usernames():
    if request.method=='GET':
        """ return a block of usernames to crawl repos for"""

    elif request.method=='POST':
        """ add or update usernames (from user crawler) """

    return ''

@api.route('/github/<id>/next_users', methods=['GET'])
def github_get_next_users():
    """ return a block of usernames to crawl """
    return ''


@api.route('/github/<id>/repos', methods=['POST'])
def github_repos():
    """ endpoint to post crawled repos to """
    return ''
