import requests


def is_reachable(url, timeout=0.001, allow_redirects=True, n_tries=3):
    """
    Determines if the provided URL is reachable

    :param url: URL to test
    :param timeout: Seconds to wait before failing (should be small)
    :param allow_redirects: If 3xx code shouldn't be treated as the final code
    :param n_tries: Max number of times to retry connection before fail
    :return: bool
    """
    for _ in range(n_tries):
        try:
            resp = requests.head(url, timeout=timeout,
                                 allow_redirects=allow_redirects)
            if resp.status_code == 200:
                return True
        except Exception as e:
            pass
    return False
