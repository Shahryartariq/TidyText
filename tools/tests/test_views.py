import json
import re

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from tools.catalog import TOOLS
from tools.views import MAX_INPUT_CHARS


class PageTests(SimpleTestCase):
    def test_home_renders_with_example_already_cleaned(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Clean up messy text in seconds</h1>", html=True)
        self.assertContains(response, 'rel="canonical" href="http://testserver/"')
        self.assertContains(response, "TidyText fixes it.")

    def test_every_tool_page_renders_with_its_own_metadata(self):
        titles = set()
        for tool in TOOLS:
            with self.subTest(tool.slug):
                response = self.client.get(reverse("tool", args=[tool.slug]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f"<title>{tool.title}</title>")
                self.assertContains(response, f"/{tool.slug}/")
                self.assertLessEqual(len(tool.title), 65, "title too long for search results")
                self.assertLessEqual(len(tool.description), 170, "description too long")
                titles.add(tool.title)
        self.assertEqual(len(titles), len(TOOLS), "every tool needs a unique title")

    def test_tool_presets_are_preselected(self):
        response = self.client.get("/uppercase-converter/")
        self.assertContains(response, '<option value="upper" selected>')
        response = self.client.get("/fix-pdf-line-breaks/")
        self.assertContains(response, 'value="paragraphs" checked')

    def test_structured_data_is_valid_json(self):
        response = self.client.get("/remove-line-breaks/")
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.text, re.S)
        data = json.loads(match.group(1))
        types = {item["@type"] for item in data}
        self.assertEqual(types, {"WebApplication", "FAQPage", "BreadcrumbList"})

    def test_static_pages(self):
        for name in ("about", "privacy"):
            with self.subTest(name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_unknown_page_is_a_friendly_404(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page doesn't exist", status_code=404)

    def test_robots_and_sitemap(self):
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Sitemap: http://testserver/sitemap.xml")
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        for tool in TOOLS:
            self.assertContains(sitemap, f"/{tool.slug}/</loc>")

    def test_healthz(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.content, b"ok")
        self.assertIn("no-cache", response["Cache-Control"])

    def test_favicon_redirects_to_static_file(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("/static/img/favicon.ico"))


class FormFallbackTests(SimpleTestCase):
    """The form works without JavaScript by posting to the server."""

    def test_post_formats_text(self):
        response = self.client.post(
            "/",
            {
                "text": "hello   WORLD\nagain",
                "line_breaks": "remove",
                "case": "title",
                "flags": ["remove_extra_spaces"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">Hello World Again</textarea>")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_output_is_html_escaped(self):
        response = self.client.post("/", {"text": "<script>alert(1)</script>", "case": "upper"})
        self.assertNotContains(response, "<SCRIPT>")
        self.assertContains(response, "&lt;SCRIPT&gt;")

    def test_empty_text_shows_an_error(self):
        response = self.client.post("/", {"text": "   "})
        self.assertContains(response, "Paste some text first", status_code=400)

    def test_too_long_text_is_rejected(self):
        response = self.client.post("/", {"text": "a" * (MAX_INPUT_CHARS + 1)})
        self.assertContains(response, "That text is too long", status_code=413)

    def test_bad_option_values_are_ignored(self):
        response = self.client.post("/", {"text": "Keep", "line_breaks": "x", "case": "y", "flags": "z"})
        self.assertContains(response, ">Keep</textarea>")

    def test_other_methods_are_not_allowed(self):
        self.assertEqual(self.client.put("/").status_code, 405)


@override_settings(DEBUG=False)
class SecurityHeaderTests(SimpleTestCase):
    def test_security_headers(self):
        response = self.client.get("/")
        csp = response["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertIn("camera=()", response["Permissions-Policy"])

    def test_pages_set_no_cookies_and_are_cacheable(self):
        response = self.client.get("/remove-extra-spaces/")
        self.assertFalse(response.cookies)
        self.assertIn("s-maxage=86400", response["Cache-Control"])
        self.assertIn("public", response["Cache-Control"])
