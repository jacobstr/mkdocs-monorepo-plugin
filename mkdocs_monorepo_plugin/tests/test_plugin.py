#!/usr/bin/env python

import unittest
import os
import tempfile

from mkdocs_monorepo_plugin import plugin as p
from mkdocs_monorepo_plugin.parser import IncludeNavLoader


class MockServer:
    """MockServer tracks what the livereload.Server instance is watching."""

    def __init__(self):
        self.watched = []

    def watch(self, input):
        self.watched.append(input)


class TestMonorepoPlugin(unittest.TestCase):
    def test_plugin_on_config_defaults(self):
        plugin = p.MonorepoPlugin()
        plugin.on_config({})
        self.assertIsNone(plugin.originalDocsDir)

    def test_plugin_on_config_with_nav(self):
        plugin = p.MonorepoPlugin()
        plugin.on_config({"nav": {"page1": "page1.md"}, "docs_dir": "docs"})
        self.assertEqual(plugin.originalDocsDir, "docs")

    def test_plugin_on_serve_no_run(self):
        plugin = p.MonorepoPlugin()
        plugin.originalDocsDir = None
        server = MockServer()
        plugin.on_serve(server, {})
        self.assertEqual(server.watched, [])

    def test_plugin_on_serve(self):
        plugin = p.MonorepoPlugin()
        plugin.originalDocsDir = "docs"
        plugin.resolvedPaths = []
        server = MockServer()
        plugin.on_serve(server, {})
        self.assertSetEqual(set(server.watched), {"docs"})


class TestAnchorBasedPartialNavInclusion(unittest.TestCase):
    """Tests for anchor-based partial navigation inclusion feature."""

    def setUp(self):
        """Create a temporary directory with test mkdocs.yml files."""
        self.test_dir = tempfile.mkdtemp()
        self.mkdocs_file = os.path.join(self.test_dir, "mkdocs.yml")

        # Create a test mkdocs.yml with multiple nav sections
        with open(self.mkdocs_file, 'w') as f:
            f.write("""site_name: TestSite
docs_dir: docs
nav:
  - Home: index.md
  - Guides:
    - Getting Started: guides/getting-started.md
    - Advanced: guides/advanced.md
  - Reference:
    - API: reference/api.md
    - CLI: reference/cli.md
""")

        # Create docs directory
        os.makedirs(os.path.join(self.test_dir, "docs"))

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_anchor_parsing(self):
        """Test that anchors are correctly parsed from include paths."""
        config = {"config_file_path": self.mkdocs_file}

        # Test with anchor
        loader = IncludeNavLoader(config, "mkdocs.yml#Guides")
        self.assertEqual(loader.navPath, "mkdocs.yml")
        self.assertEqual(loader.navSection, "Guides")

        # Test without anchor
        loader_no_anchor = IncludeNavLoader(config, "mkdocs.yml")
        self.assertEqual(loader_no_anchor.navPath, "mkdocs.yml")
        self.assertIsNone(loader_no_anchor.navSection)

    def test_extract_nav_section(self):
        """Test that specific nav sections can be extracted."""
        config = {"config_file_path": self.mkdocs_file}
        loader = IncludeNavLoader(config, "mkdocs.yml#Guides")
        loader.read()

        # The extracted nav should only contain the Guides section content
        nav = loader.getNav()

        # Check that we got a list (the content of the Guides section)
        self.assertIsInstance(nav, list)

        # The nav should contain items from the Guides section
        self.assertTrue(len(nav) > 0)

    def test_unique_alias_with_section(self):
        """Test that aliases are unique when sections are specified."""
        config = {"config_file_path": self.mkdocs_file}

        # Load with section anchor
        loader_with_section = IncludeNavLoader(config, "mkdocs.yml#Guides")
        loader_with_section.read()
        alias_with_section = loader_with_section.getAlias()

        # Load without section anchor
        loader_without_section = IncludeNavLoader(config, "mkdocs.yml")
        loader_without_section.read()
        alias_without_section = loader_without_section.getAlias()

        # Aliases should be different
        self.assertNotEqual(alias_with_section, alias_without_section)
        self.assertIn("Guides", alias_with_section)

    def test_section_not_found(self):
        """Test that an error is raised when the specified section doesn't exist."""
        config = {"config_file_path": self.mkdocs_file}
        loader = IncludeNavLoader(config, "mkdocs.yml#NonExistentSection")

        with self.assertRaises(SystemExit):
            loader.read()
            loader.getNav()
