import tomllib
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class PackagingTests(SimpleTestCase):
    def test_pyproject_and_requirements_list_the_same_dependencies(self):
        """Vercel installs from pyproject.toml and Docker from requirements.txt."""
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        declared = {dep.lower() for dep in pyproject["project"]["dependencies"]}
        lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        required = {line.strip().lower() for line in lines if line.strip() and not line.startswith("#")}
        self.assertTrue(declared, "pyproject.toml must list the runtime dependencies")
        self.assertEqual(declared, required)

    def test_vercel_entry_point_exposes_the_wsgi_app(self):
        source = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        self.assertIn("app = application", source)
