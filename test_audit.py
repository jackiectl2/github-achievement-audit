import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from audit import fetch_snapshot, render_markdown


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class AuditTests(unittest.TestCase):
    def test_public_snapshot_excludes_forks_and_keeps_pr_count_labeled(self):
        requested = []

        def opener(request, timeout):
            self.assertEqual(timeout, 20)
            requested.append(request.full_url)
            if "/repos?" in request.full_url:
                payload = [
                    {"full_name": "alice/tool", "fork": False, "stargazers_count": 17},
                    {"full_name": "alice/upstream-copy", "fork": True, "stargazers_count": 5000},
                ]
            else:
                payload = {"total_count": 23, "items": []}
            return FakeResponse(json.dumps(payload).encode())

        snapshot = fetch_snapshot("alice", opener=opener)
        self.assertEqual(snapshot.owned_public_repo_count, 1)
        self.assertEqual(snapshot.top_owned_repo, "alice/tool")
        self.assertEqual(snapshot.top_owned_repo_stars, 17)
        self.assertEqual(snapshot.public_authored_merged_pr_search_total, 23)
        self.assertEqual(len(requested), 2)
        self.assertIn("is:public", parse_qs(urlsplit(requested[1]).query)["q"][0])
        self.assertIn("not badge eligibility counts", render_markdown(snapshot))

    def test_invalid_username_is_rejected_before_network_request(self):
        with self.assertRaises(ValueError):
            fetch_snapshot("alice/../../bad", opener=lambda *_args, **_kwargs: self.fail("network called"))


if __name__ == "__main__":
    unittest.main()
