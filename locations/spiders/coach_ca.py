from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CoachCASpider(SitemapSpider, StructuredDataSpider):
    name = "coach_ca"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = ["https://ca.coach.com/sitemap_index.xml"]
    sitemap_follow = [r"/en/"]
    sitemap_rules = [(r"/en/stores/(outlets/)?\w\w/[-\w]+/.+$", "parse_sd")]
    wanted_types = ["Store", "OutletStore"]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["extras"]["website:fr"] = response.urljoin(response.xpath('//a[text()="Français"]/@href').get())
        item["extras"]["website:en"] = response.url

        if item["name"].startswith("COACH Outlet"):
            item["name"] = "COACH Outlet"
        else:
            item["name"] = "COACH"

        item["branch"] = ld_data["name"].removeprefix(item["name"]).strip()

        yield item
