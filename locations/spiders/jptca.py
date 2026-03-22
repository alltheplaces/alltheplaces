import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class JptcaSpider(SitemapSpider):
    name = "jptca"
    item_attributes = {"operator": "日本交通文化協会", "operator_wikidata": "Q41698337"}
    sitemap_urls = ["https://jptca.org/page-sitemap.xml"]
    sitemap_rules = [("/publicart", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        if latlon := re.search(r"LatLng\(\s*(\d+\.\d+),(\d+\.\d+)\);", response.text):  # only get items with location
            item["lat"], item["lon"] = latlon.groups()
        else:
            return
        item["ref"] = "".join(filter(str.isdigit, response.url))
        item["website"] = response.url
        item["extras"]["website:en"] = f"https://jptca.org/en/publicart{item['ref']}/"
        item["extras"]["operator:en"] = "Japan Traffic Culture Association"
        if nm := re.search(r"(?:<\/div>「)(.+?)」", response.text):
            item["name"] = nm.group(1)

        if hira := re.search(r'kana">(.+)<\/', response.text):
            item["extras"]["name:ja-Hira"] = hira.group(1)

        if img := re.search(r"background-image:url\('(.+sakuhin.jpg)'", response.text):
            if item["ref"] in img.group(1):
                item["image"] = "https://jptca.org" + img.group(1)

        item["extras"]["tourism"] = "artwork"
        yield item
