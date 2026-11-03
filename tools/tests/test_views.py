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


class NewToolTests(SimpleTestCase):
    def test_word_counter_opens_the_stats_panel(self):
        response = self.client.get("/word-counter/")
        self.assertContains(response, '<details class="more-stats" open>')
        self.assertContains(response, 'data-detail="reading_seconds"')

    def test_find_and_replace_page_opens_the_panel_with_a_preset(self):
        response = self.client.get("/find-and-replace/")
        self.assertContains(response, '<details class="find-replace" open>')
        self.assertContains(response, 'value="colour"')
        self.assertContains(response, "The color of the sky changes color at sunset.")

    def test_post_sort_dedupe_and_find_replace(self):
        response = self.client.post(
            "/",
            {
                "text": "pear\napple\npear\nfig",
                "sort": "az",
                "flags": ["remove_duplicate_lines"],
                "find": "fig",
                "replace": "kiwi",
            },
        )
        self.assertContains(response, ">apple\nkiwi\npear</textarea>")

    def test_ai_paraphraser_is_offered_only_where_set(self):
        for path in ("/paraphrasing-tool/", "/ai-text-humanizer/"):
            with self.subTest(path):
                response = self.client.get(path)
                self.assertContains(response, "data-ai ")
                self.assertContains(response, "js/ai-worker.js?v=")
                csp = response["Content-Security-Policy"]
                self.assertIn("worker-src 'self' https://cdn.jsdelivr.net", csp)
        home = self.client.get("/")
        self.assertNotContains(home, "data-ai ")
        self.assertNotIn("jsdelivr", home["Content-Security-Policy"])

    def test_paraphrase_runs_without_javascript(self):
        response = self.client.post(
            "/paraphrasing-tool/", {"text": "We are able to help.", "flags": ["paraphrase"]}
        )
        self.assertContains(response, ">We can help.</textarea>")

    def test_example_text_is_labelled_only_before_posting(self):
        self.assertContains(self.client.get("/"), "data-example-tag")
        self.assertNotContains(self.client.post("/", {"text": "Mine"}), "data-example-tag")

    def test_text_that_needs_no_changes_says_so(self):
        response = self.client.post("/", {"text": "Already tidy.", "flags": ["remove_extra_spaces"]})
        self.assertContains(response, "Already clean, nothing to change")
        response = self.client.post("/", {"text": "tidy", "case": "upper"})
        self.assertNotContains(response, "Already clean")

    def test_no_options_shows_counts_not_already_clean(self):
        response = self.client.get("/word-counter/")
        self.assertNotContains(response, "Already clean")
        self.assertContains(response, " words</span>")

    def test_post_strip_html_never_renders_markup(self):
        response = self.client.post("/", {"text": "<img src=x onerror=alert(1)>Hi", "flags": ["strip_html"]})
        self.assertContains(response, ">Hi</textarea>")
        self.assertNotContains(response, "<img src=x")


class AnalyticsTests(SimpleTestCase):
    def test_no_analytics_by_default(self):
        response = self.client.get("/")
        self.assertNotContains(response, "googletagmanager")
        self.assertContains(self.client.get("/privacy/"), "no analytics")

    def test_analytics_tag_and_csp_when_configured(self):
        from tidytext.settings import build_csp

        with self.settings(GA_MEASUREMENT_ID="G-TEST12345", SECURE_CSP=build_csp(analytics=True)):
            response = self.client.get("/")
            self.assertContains(response, 'src="https://www.googletagmanager.com/gtag/js?id=G-TEST12345"')
            self.assertContains(response, 'data-ga-id="G-TEST12345"')
            csp = response["Content-Security-Policy"]
            self.assertIn("script-src 'self' https://www.googletagmanager.com", csp)
            self.assertNotIn("unsafe-inline", csp)
            self.assertContains(self.client.get("/privacy/"), "Google Analytics")
