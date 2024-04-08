import json
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KekeSpider(SitemapSpider, StructuredDataSpider):
    name = "keke"
    item_attributes = {"brand": "Keke's Breakfast Cafe", "brand_wikidata": "Q115930150"}
    allowed_domains = ["kekes.com"]
    sitemap_urls = ["https://www.kekes.com/sitemap.xml"]
    sitemap_rules = [("/kekes-", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data):
        if response.xpath('//div[@class="sqs-block-content"]/p[1]/text()').get() == "COMING SOON!":
            return
        data = json.loads(response.xpath("//@data-block-json").get()).get("location", {})
        item["name"] = response.xpath('//div[@class="sqs-block-content"]//h1/text()').get()
        if address := response.xpath(
            '//a[contains(@href, "maps/place/") or contains(@href, "/g.page/") or contains(@href, "/maps?q")]/text()'
        ).extract():
            item["housenumber"] = (re.findall(r"^\d+", address[0].strip())[:1] or (None,))[0]
            item["street_address"] = address[0].strip()
            item["city"] = address[-1].split(",")[0]
            item["state"] = address[-1].split(",")[1].split()[0]
            item["postcode"] = address[-1].split(",")[1].split()[1]
        item["country"] = data.get("addressCountry")
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["phone"] = response.xpath('//a[contains(@href, "tel")]/text()').get()
        item["lat"] = data.get("mapLat")
        item["lon"] = data.get("mapLng")

        yield item
