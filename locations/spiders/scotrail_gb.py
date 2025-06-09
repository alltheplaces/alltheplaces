import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class ScotrailGBSpider(SitemapSpider):
    name = "scotrail_gb"
    item_attributes = {"operator": "ScotRail", "operator_wikidata": "Q18356161"}
    sitemap_urls = ["https://www.scotrail.co.uk/default/sub/sitemaps/content--station/sitemap.xml"]
    sitemap_rules = [(r"/plan-your-journey", "parse")]
    requires_proxy = True

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["extras"]["ref:crs"] = response.url.split("/")[-1]
        item["name"] = response.xpath("//h1/text()").get().replace("Station", "").strip()
        item["lat"] = re.search(r'"lat":(-?\d+\.\d+),', response.text).group(1)
        item["lon"] = re.search(r'"lon":(-?\d+\.\d+),', response.text).group(1)
        item["website"] = response.url

        apply_category(Categories.TRAIN_STATION, item)

        yield item
