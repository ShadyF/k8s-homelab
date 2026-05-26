import importlib.util
import os
import pathlib
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "fetch_pr_upgrade_inventory.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_pr_upgrade_inventory", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FetchPrUpgradeInventoryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_extract_release_links_from_markdown_and_plain_urls(self):
        body = """
        Release notes: [v1.2.3](https://github.com/example/app/releases/tag/v1.2.3)
        Changelog: https://example.com/changelog#123
        Homepage: https://example.com/docs
        """

        links = self.module.extract_release_links(body)

        self.assertEqual(
            links,
            [
                "https://github.com/example/app/releases/tag/v1.2.3",
                "https://example.com/changelog#123",
            ],
        )

    def test_extract_versions_from_renovate_title(self):
        versions = self.module.extract_versions(
            "chore(deps): update ghcr.io/example/app docker tag v1.2.3 to v1.3.0",
            "",
            [],
        )

        self.assertEqual(versions["current_version"], "v1.2.3")
        self.assertEqual(versions["target_version"], "v1.3.0")

    def test_extract_versions_from_patch_when_title_is_generic(self):
        files = [
            {
                "filename": "cluster/apps/media/example/helmrelease.yaml",
                "patch": "@@\n-    version: 1.2.3\n+    version: 1.3.0\n",
            }
        ]

        versions = self.module.extract_versions("Update example chart", "", files)

        self.assertEqual(versions["current_version"], "1.2.3")
        self.assertEqual(versions["target_version"], "1.3.0")

    def test_build_inventory_item_shapes_pr_data(self):
        pr = {
            "number": 42,
            "title": "chore(deps): update example chart 1.2.3 to 1.3.0",
            "html_url": "https://github.com/ShadyF/k8s-homelab/pull/42",
            "body": "Release notes: https://github.com/example/chart/releases/tag/1.3.0",
            "user": {"login": "renovate[bot]"},
            "head": {"ref": "renovate/example-1.x"},
            "base": {"ref": "master"},
        }
        files = [
            {
                "filename": "cluster/apps/media/example/helmrelease.yaml",
                "status": "modified",
                "patch": "@@\n-    version: 1.2.3\n+    version: 1.3.0\n",
            }
        ]
        commits = [{"sha": "abc123", "commit": {"message": "update example"}}]

        item = self.module.build_inventory_item(pr, files, commits)

        self.assertEqual(item["number"], 42)
        self.assertEqual(item["title"], pr["title"])
        self.assertEqual(item["url"], pr["html_url"])
        self.assertEqual(item["changed_files"], ["cluster/apps/media/example/helmrelease.yaml"])
        self.assertEqual(item["current_version"], "1.2.3")
        self.assertEqual(item["target_version"], "1.3.0")
        self.assertEqual(item["release_links"], ["https://github.com/example/chart/releases/tag/1.3.0"])
        self.assertEqual(item["commit_messages"], ["update example"])
        self.assertEqual(item["body"], pr["body"])
        self.assertEqual(
            item["version_detection"],
            {
                "current_version": "1.2.3",
                "target_version": "1.3.0",
                "source": "title",
                "confidence": "heuristic",
                "candidates": [
                    {"current_version": "1.2.3", "target_version": "1.3.0", "source": "title"}
                ],
            },
        )
        self.assertEqual(
            item["files"],
            [
                {
                    "filename": "cluster/apps/media/example/helmrelease.yaml",
                    "status": "modified",
                    "additions": None,
                    "deletions": None,
                    "changes": None,
                    "patch": "@@\n-    version: 1.2.3\n+    version: 1.3.0\n",
                }
            ],
        )
        self.assertEqual(
            item["commits"],
            [{"sha": "abc123", "message": "update example", "html_url": None}],
        )

    def test_auth_header_uses_github_token_when_available(self):
        old = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "token-value"
        try:
            headers = self.module.github_headers()
        finally:
            if old is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = old

        self.assertEqual(headers["Authorization"], "Bearer token-value")
        self.assertEqual(headers["Accept"], "application/vnd.github+json")


if __name__ == "__main__":
    unittest.main()
