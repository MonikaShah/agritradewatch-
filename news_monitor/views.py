from django.shortcuts import render
from django.http import HttpResponse

import csv
import json
import urllib.parse
import feedparser
from deep_translator import GoogleTranslator

from collections import Counter
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


LANGUAGE_CONFIG = {

    "en": {
        "hl": "en-IN",
        "ceid": "IN:en"
    },

    "hi": {
        "hl": "hi",
        "ceid": "IN:hi"
    },

    "mr": {
        "hl": "mr",
        "ceid": "IN:mr"
    }

}

def get_search_terms(keyword, selected_language):

    if selected_language == "en":
        return [keyword]

    elif selected_language == "hi":

        try:

            translated = GoogleTranslator(
                source='auto',
                target='hi'
            ).translate(keyword)

            return [keyword, translated]

        except:

            return [keyword]

    elif selected_language == "mr":

        try:

            translated = GoogleTranslator(
                source='auto',
                target='mr'
            ).translate(keyword)

            return [keyword, translated]

        except:

            return [keyword]

    else:

        terms = [keyword]

        try:
            terms.append(
                GoogleTranslator(
                    source='auto',
                    target='hi'
                ).translate(keyword)
            )
        except:
            pass

        try:
            terms.append(
                GoogleTranslator(
                    source='auto',
                    target='mr'
                ).translate(keyword)
            )
        except:
            pass

        return list(set(terms))

def dashboard(request):

    articles = []
    keywords = []
    selected_language = "all"

    if request.method == "POST":

        selected_language = request.POST.get(
            "language",
            "all"
        )

        keywords_text = request.POST.get(
            "keywords",
            ""
        )

        keywords = [
            x.strip()
            for x in keywords_text.splitlines()
            if x.strip()
        ]

        for keyword in keywords:

            if selected_language == "all":

                languages = ["en", "hi", "mr"]

            else:

                languages = [selected_language]

            search_terms = get_search_terms(
                keyword,
                selected_language
            )

        for search_term in search_terms:

            for lang_code in languages:

                lang = LANGUAGE_CONFIG[lang_code]

                rss_url = (
                    "https://news.google.com/rss/search?"
                    f"q={urllib.parse.quote(search_term)}"
                    f"&hl={lang['hl']}"
                    "&gl=IN"
                    f"&ceid={lang['ceid']}"
                )

                print("=" * 60)
                print("Original Keyword:", keyword)
                print("Search Term:", search_term)
                print("Language:", lang_code)
                print(rss_url)

                feed = feedparser.parse(rss_url)

                for entry in feed.entries:

                    source = ""

                    try:
                        source = entry.source.title
                    except:
                        pass

                    articles.append({
                        "keyword": keyword,
                        "language": lang_code,
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", ""),
                        "source": source
                    })

    # Remove duplicates

    seen = set()
    unique_articles = []

    for article in articles:

        if article["url"] not in seen:

            seen.add(article["url"])
            unique_articles.append(article)

    articles = unique_articles

    # Sort by newest

    def get_sort_date(article):

        try:

            return parsedate_to_datetime(
                article["published"]
            ).astimezone(timezone.utc)

        except:

            return datetime(
                1900,
                1,
                1,
                tzinfo=timezone.utc
            )

    articles.sort(
        key=get_sort_date,
        reverse=True
    )

    # Format dates

    for article in articles:

        try:

            dt = parsedate_to_datetime(
                article["published"]
            )

            article["published_display"] = dt.strftime(
                "%d %b %Y %H:%M"
            )

        except:

            article["published_display"] = (
                article["published"]
            )

    request.session["articles"] = articles

    total_articles = len(articles)

    source_counter = Counter(
        [
            a["source"]
            for a in articles
            if a["source"]
        ]
    )

    chart_labels = list(
        source_counter.keys()
    )[:10]

    chart_values = list(
        source_counter.values()
    )[:10]

    keyword_stats = {}

    for keyword in keywords:

        keyword_stats[keyword] = sum(
            1
            for a in articles
            if a["keyword"] == keyword
        )

    context = {

        "articles": articles,

        "total_articles": total_articles,

        "source_count": len(
            source_counter
        ),

        "keyword_stats": keyword_stats,

        "selected_language":
            selected_language,

        "chart_labels_json":
            json.dumps(chart_labels),

        "chart_values_json":
            json.dumps(chart_values),

    }

    return render(
        request,
        "news_monitor/dashboard.html",
        context
    )


def download_csv(request):

    articles = request.session.get(
        "articles",
        []
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; filename="news.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Keyword",
        "Language",
        "Source",
        "Title",
        "Published",
        "URL"
    ])

    for a in articles:

        writer.writerow([
            a["keyword"],
            a["language"],
            a["source"],
            a["title"],
            a["published"],
            a["url"]
        ])

    return response