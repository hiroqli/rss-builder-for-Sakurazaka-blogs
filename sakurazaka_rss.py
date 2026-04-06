#!/usr/bin/env python3
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import re

BASE_URL = "https://sakurazaka46.com"
BLOG_LIST_URL = f"{BASE_URL}/s/s46/diary/blog/list?ima=0000"
JST = timezone(timedelta(hours=9))


class BlogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self._in_blog_part = False
        self._current = {}
        self._capture = None
        self._depth = 0
        self._blog_part_depth = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._depth += 1

        if tag == "ul" and "com-blog-part" in attrs.get("class", ""):
            self._in_blog_part = True
            self._blog_part_depth = self._depth

        if not self._in_blog_part:
            return

        if tag == "a" and "href" in attrs:
            href = attrs["href"]
            m = re.search(r"/diary/detail/(\d+)", href)
            if m:
                self._current = {
                    "id": m.group(1),
                    "url": BASE_URL + re.sub(r"\?.*", "", href),
                }

        if tag == "p" and attrs.get("class") == "name":
            self._capture = "name"

        if tag == "p" and attrs.get("class", "").startswith("date"):
            self._capture = "date"

        if tag == "h3" and attrs.get("class") == "title":
            self._capture = "title"

        if tag == "p" and attrs.get("class") == "lead":
            self._capture = "lead"

    def handle_endtag(self, tag):
        self._depth -= 1
        self._capture = None

        if self._in_blog_part and tag == "li" and self._current.get("title"):
            self.entries.append(self._current)
            self._current = {}

        if self._in_blog_part and self._blog_part_depth and self._depth < self._blog_part_depth:
            self._in_blog_part = False

    def handle_data(self, data):
        if not self._capture or not self._current:
            return
        data = data.strip()
        if not data:
            return
        self._current[self._capture] = self._current.get(self._capture, "") + data
        if self._capture != "lead":
            self._capture = None


def parse_date(date_str, now):
    # "2026/4/05 12:34" or "2026/4/05" -> datetime
    try:
        return datetime.strptime(date_str.strip(), "%Y/%m/%d %H:%M").replace(tzinfo=JST)
    except ValueError:
        pass
    try:
        dt = datetime.strptime(date_str.strip(), "%Y/%m/%d")
        return dt.replace(hour=now.hour, minute=now.minute, second=now.second, tzinfo=JST)
    except ValueError:
        pass
    return now


def build_rss(entries):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "櫻坂46 OFFICIAL BLOG"
    ET.SubElement(channel, "link").text = BLOG_LIST_URL
    ET.SubElement(channel, "description").text = "櫻坂46公式ブログ"
    ET.SubElement(channel, "language").text = "ja"
    now = datetime.now(JST)
    ET.SubElement(channel, "lastBuildDate").text = now.strftime(
        "%a, %d %b %Y %H:%M:%S %z"
    )
    for e in entries:
        item = ET.SubElement(channel, "item")
        title = f"{e.get('name', '')} - {e.get('title', '')}"
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = e["url"]
        ET.SubElement(item, "guid", isPermaLink="true").text = e["url"]
        ET.SubElement(item, "description").text = e.get("lead", "")
        pub_date = parse_date(e.get("date", ""), now)
        ET.SubElement(item, "pubDate").text = pub_date.strftime(
            "%a, %d %b %Y %H:%M:%S %z"
        )

    return ET.tostring(rss, encoding="unicode", xml_declaration=True)


def main():
    req = urllib.request.Request(
        BLOG_LIST_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; sakurazaka-rss/1.0)"},
    )
    with urllib.request.urlopen(req) as res:
        html = res.read().decode("utf-8")

    parser = BlogParser()
    parser.feed(html)

    rss_xml = build_rss(parser.entries)

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"Generated feed.xml with {len(parser.entries)} entries")
    for e in parser.entries[:3]:
        print(f"  {e.get('date')} {e.get('name')} - {e.get('title')}")


if __name__ == "__main__":
    main()
