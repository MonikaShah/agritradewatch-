from django.shortcuts import render
from django.http import HttpResponse

import csv
import json
import urllib.parse
import feedparser
from deep_translator import GoogleTranslator

from collections import Counter
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone,timedelta
from collections import defaultdict

def build_timeline(articles):
    timeline = defaultdict(int)

    for a in articles:
        date_str = a.get("published")   # FIX HERE

        if date_str:
            try:
                dt = parsedate_to_datetime(date_str)
                day = dt.strftime("%Y-%m-%d")
                timeline[day] += 1
            except:
                pass

    sorted_data = sorted(timeline.items())

    labels = [x[0] for x in sorted_data]
    values = [x[1] for x in sorted_data]

    return labels, values

def generate_ai_insights(articles):
    insights = []

    if not articles:
        return ["No data available for analysis"]

    # ----------------------------
    # 1. Keyword dominance
    # ----------------------------
    keywords = [a.get("keyword") for a in articles if a.get("keyword")]
    keyword_counts = Counter(keywords)

    top_keyword = keyword_counts.most_common(1)[0]

    insights.append(
        f"🔥 Dominant topic: '{top_keyword[0]}' appears {top_keyword[1]} times"
    )

    # ----------------------------
    # 2. Source concentration
    # ----------------------------
    sources = [a.get("source") for a in articles if a.get("source")]
    source_counts = Counter(sources)

    top_source = source_counts.most_common(1)[0]

    insights.append(
        f"📰 Most active source: {top_source[0]} ({top_source[1]} articles)"
    )

    # ----------------------------
    # 3. Freshness (last 24h spike proxy)
    # ----------------------------
    now = datetime.now()
    last_24h = [
        a for a in articles
        if a.get("published_date")
        and (now - a["published_date"]).days <= 1
    ]

    if len(last_24h) > len(articles) * 0.5:
        insights.append("⚠️ High activity spike in last 24 hours")

    # ----------------------------
    # 4. Repetition signal (possible event cluster)
    # ----------------------------
    repeated = [k for k, v in keyword_counts.items() if v >= 3]

    if repeated:
        insights.append(
            f"📌 Repeating clusters detected: {', '.join(repeated)}"
        )

    return insights
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
    insights = generate_ai_insights(articles)
    labels, values = build_timeline(articles)
    context = {

        "articles": articles,

        "insights": insights,

        "timeline_labels_json": json.dumps(labels),
        "timeline_values_json": json.dumps(values),

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