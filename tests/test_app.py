import json
import shutil
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path

from prompt_builder.config import AppConfig
from prompt_builder.models import PromptItem
from prompt_builder.repository import FileSystemPromptRepository, InvalidFilenameError
from prompt_builder.services import PromptService
from prompt_builder.server import create_server


class TestPromptModels(unittest.TestCase):
    def test_parse_markdown_with_frontmatter(self):
        content = """---
title: Custom Prompt
description: A helpful description
tags: testing, mock
---

# Headline

This is body line 1.
This is body line 2.
"""
        item = PromptItem.parse_markdown("custom.md", content, "prompt")
        self.assertEqual(item.title, "Custom Prompt")
        self.assertEqual(item.description, "A helpful description")
        self.assertEqual(item.tags, ["testing", "mock"])
        self.assertIn("This is body line 1.", item.preview)

    def test_parse_markdown_without_frontmatter(self):
        content = """# First Heading
Here is the text for this prompt.
"""
        item = PromptItem.parse_markdown("hello_world.md", content, "prompt")
        self.assertEqual(item.title, "First Heading")
        self.assertEqual(item.tags, [])
        self.assertIn("Here is the text", item.preview)

    def test_fallback_title_from_filename(self):
        content = "Just plain text without headers."
        item = PromptItem.parse_markdown("my_sample_prompt.md", content, "appendix")
        self.assertEqual(item.title, "My Sample Prompt")
        self.assertEqual(item.item_type, "appendix")


class TestPromptRepository(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.prompts_dir = Path(self.test_dir) / "prompts"
        self.appendices_dir = Path(self.test_dir) / "appendices"
        self.repo = FileSystemPromptRepository(self.prompts_dir, self.appendices_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_and_get_item(self):
        saved = self.repo.save_item("prompt", "test1.md", "# Test Prompt\nContent here")
        self.assertEqual(saved.filename, "test1.md")
        self.assertEqual(saved.title, "Test Prompt")

        retrieved = self.repo.get_item("prompt", "test1.md")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "# Test Prompt\nContent here")

    def test_list_and_delete_item(self):
        self.repo.save_item("appendix", "app1.md", "Appendix 1")
        self.repo.save_item("appendix", "app2.md", "Appendix 2")

        items = self.repo.list_items("appendix")
        self.assertEqual(len(items), 2)

        deleted = self.repo.delete_item("appendix", "app1.md")
        self.assertTrue(deleted)

        items_after = self.repo.list_items("appendix")
        self.assertEqual(len(items_after), 1)
        self.assertEqual(items_after[0].filename, "app2.md")

    def test_path_traversal_prevention(self):
        with self.assertRaises(InvalidFilenameError):
            self.repo.get_item("prompt", "../secret.md")

        with self.assertRaises(InvalidFilenameError):
            self.repo.save_item("prompt", "../../escape.md", "data")


class TestPromptService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo = FileSystemPromptRepository(
            Path(self.test_dir) / "prompts",
            Path(self.test_dir) / "appendices",
        )
        self.service = PromptService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_seeding_defaults(self):
        prompts = self.service.list_prompts()
        appendices = self.service.list_appendices()
        self.assertGreater(len(prompts), 0)
        self.assertGreater(len(appendices), 0)

    def test_search_filtering(self):
        results = self.service.list_prompts(query="code")
        self.assertTrue(any("code" in p["title"].lower() or "code" in str(p.get("tags", [])) for p in results))

    def test_compose_prompt(self):
        self.service.save_appendix("rule1.md", "Rule 1 Content")
        self.service.save_appendix("rule2.md", "Rule 2 Content")
        composed = self.service.compose_prompt(
            base_content="Base Instructions",
            appendix_filenames=["rule1.md", "rule2.md"],
            separator="\n---\n",
        )
        self.assertIn("Base Instructions", composed)
        self.assertIn("Rule 1 Content", composed)
        self.assertIn("Rule 2 Content", composed)


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        base_dir = Path(__file__).resolve().parent.parent
        static_dir = base_dir / "prompt_builder" / "static"

        cls.config = AppConfig(
            base_dir=Path(cls.test_dir),
            prompts_dir=Path(cls.test_dir) / "prompts",
            appendices_dir=Path(cls.test_dir) / "appendices",
            static_dir=static_dir,
            host="127.0.0.1",
            port=8765,
        )
        cls.repo = FileSystemPromptRepository(cls.config.prompts_dir, cls.config.appendices_dir)
        cls.service = PromptService(cls.repo)
        cls.server = create_server(cls.config, cls.service)

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.test_dir)

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:8765{path}"

    def test_health_check(self):
        req = urllib.request.Request(self._url("/api/health"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["status"], "ok")

    def test_list_prompts_api(self):
        req = urllib.request.Request(self._url("/api/prompts"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIn("items", data)
            self.assertGreater(data["count"], 0)

    def test_create_and_delete_prompt_api(self):
        # Create
        create_req = urllib.request.Request(
            self._url("/api/prompts"),
            data=json.dumps({"filename": "api_test.md", "content": "# API Created"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(create_req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["filename"], "api_test.md")

        # Read
        get_req = urllib.request.Request(self._url("/api/prompts/api_test.md"))
        with urllib.request.urlopen(get_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["content"], "# API Created")

        # Delete
        del_req = urllib.request.Request(
            self._url("/api/prompts/api_test.md"),
            method="DELETE",
        )
        with urllib.request.urlopen(del_req) as resp:
            self.assertEqual(resp.status, 200)

        # Confirm 404 after delete
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self._url("/api/prompts/api_test.md"))
        self.assertEqual(ctx.exception.code, 404)

    def test_static_index(self):
        req = urllib.request.Request(self._url("/"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode()
            self.assertIn("Prompt Constructor", html)

    def test_static_css(self):
        req = urllib.request.Request(self._url("/static/style.css"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type"))


if __name__ == "__main__":
    unittest.main()
