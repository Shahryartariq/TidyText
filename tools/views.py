from __future__ import annotations

import json

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_GET, require_http_methods

from tools import transforms
from tools.catalog import COMMON_FAQS, HOME, TOOLS, TOOLS_BY_SLUG, Tool

MAX_INPUT_CHARS = 200_000

LINE_BREAK_CHOICES = (
    ("keep", "Keep as is"),
    ("paragraphs", "Join lines, keep paragraphs"),
    ("remove", "Remove all"),
)
CASE_CHOICES = (
    ("keep", "Keep as is"),
    ("sentence", "Sentence case"),
    ("lower", "lowercase"),
    ("upper", "UPPERCASE"),
    ("title", "Title Case"),
)
SORT_CHOICES = (
    ("keep", "Keep order"),
    ("az", "A to Z"),
    ("za", "Z to A"),
)
FLAG_CHOICES = (
    ("remove_extra_spaces", "Remove extra spaces", "Double spaces, tabs, spaces at line ends"),
    ("remove_empty_lines", "Remove empty lines", "Blank and whitespace-only lines"),
    ("remove_duplicate_lines", "Remove duplicate lines", "Keeps the first copy of each line"),
    ("fix_hyphenation", "Fix hyphenated words", "Rejoins words split across lines, like infor- mation"),
    ("remove_invisible", "Remove invisible characters", "Zero-width spaces, soft hyphens"),
    ("straighten_quotes", "Straight quotes", "Curly quotes and dashes to plain ones"),
    ("strip_html", "Remove HTML tags", "Keeps the text, removes the markup"),
    ("remove_punctuation", "Remove punctuation", "Commas, periods, quotes, dashes"),
)


def _json_ld(data: list[dict]) -> str:
    # Escape "<" so the JSON can never close the surrounding <script> tag.
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))  # noqa: S308


def _structured_data(request: HttpRequest, tool: Tool, faqs, page_url: str) -> str:
    site_url = request.site_url
    data: list[dict] = [
        {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": tool.title if tool.slug else "TidyText",
            "url": page_url,
            "description": tool.description,
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Any",
            "browserRequirements": "Requires a modern web browser",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }
    ]
    if faqs:
        data.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faqs
                ],
            }
        )
    if tool.slug:
        data.append(
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "TidyText", "item": site_url + "/"},
                    {"@type": "ListItem", "position": 2, "name": tool.name, "item": page_url},
                ],
            }
        )
    return _json_ld(data)


def _options_from_post(request: HttpRequest) -> transforms.Options:
    return transforms.Options.build(
        request.POST.get("line_breaks", "keep"),
        request.POST.get("case", "keep"),
        request.POST.getlist("flags"),
        request.POST.get("sort", "keep"),
        request.POST.get("find", ""),
        request.POST.get("replace", ""),
    )


@require_http_methods(["GET", "HEAD", "POST"])
def tool_page(request: HttpRequest, slug: str = "") -> HttpResponse:
    tool = TOOLS_BY_SLUG.get(slug) if slug else HOME
    if tool is None:
        raise Http404("Unknown tool")

    options = tool.options
    text = tool.example
    output = None
    error = ""
    status = 200

    if request.method == "POST":
        # Fallback for visitors without JavaScript. The text is formatted and returned,
        # never stored or logged.
        options = _options_from_post(request)
        text = request.POST.get("text", "")
        if len(text) > MAX_INPUT_CHARS:
            error = f"That text is too long. Paste up to {MAX_INPUT_CHARS:,} characters at a time."
            text = text[:MAX_INPUT_CHARS]
            status = 413
        elif not text.strip():
            error = "Paste some text first, then choose Clean text."
            status = 400
        else:
            output = transforms.apply(text, options)
    else:
        output = transforms.apply(text, options)

    faqs = tool.faqs + COMMON_FAQS
    page_url = request.site_url + request.path
    before = transforms.stats(text)
    after = transforms.stats(output) if output is not None else None
    details = transforms.details(output if output is not None else text)

    response = render(
        request,
        "tools/tool.html",
        {
            "tool": tool,
            "is_home": not tool.slug,
            "tools": TOOLS,
            "options": options,
            "text": text,
            "output": output if output is not None else "",
            "error": error,
            "before": before,
            "after": after,
            "details": details,
            "shown": after if after is not None else before,
            "show_details": tool.show_details,
            "show_find": tool.show_find or bool(options.find),
            "faqs": faqs,
            "line_break_choices": LINE_BREAK_CHOICES,
            "case_choices": CASE_CHOICES,
            "sort_choices": SORT_CHOICES,
            "flag_choices": FLAG_CHOICES,
            "max_chars": MAX_INPUT_CHARS,
            "structured_data": _structured_data(request, tool, faqs, page_url),
            "form_action": reverse("tool", args=[tool.slug]) if tool.slug else reverse("home"),
        },
        status=status,
    )
    if request.method == "POST":
        response["Cache-Control"] = "no-store"
    return response


@require_GET
def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html", {"tools": TOOLS})


@require_GET
def privacy(request: HttpRequest) -> HttpResponse:
    return render(request, "privacy.html", {"tools": TOOLS})


@require_GET
@cache_control(public=True, max_age=86400)
def robots_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {request.site_url}{reverse('sitemap')}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
@never_cache
def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


def page_not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return render(request, "404.html", {"tools": TOOLS}, status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    # Rendered without a request context, so it can't fail on context processors.
    from django.template.loader import get_template

    return HttpResponse(get_template("500.html").render(), status=500)
