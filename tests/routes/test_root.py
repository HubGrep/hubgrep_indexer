

class TestRoot():
    def test_root(self, test_client):
        res = test_client.get('/')
        assert res.status_code == 200
