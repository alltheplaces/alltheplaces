import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class AldiSudAUSpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_au"
    item_attributes = {"brand_wikidata": "Q41171672"}
    sitemap_urls = ["https://store.aldi.com.au/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/store\.aldi\.com\.au\/\w+\/[-\w]+\/[-\w]+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        # Opening hours in Microdata contains the hours for ""
        item["opening_hours"] = OpeningHours()
        if data := response.xpath("//@data-days").get():
            for rule in json.loads(data):
                if rule["isClosed"]:
                    item["opening_hours"].set_closed(rule["day"])
                for time in rule["intervals"]:
                    item["opening_hours"].add_range(
                        rule["day"], str(time["start"]).zfill(4), str(time["end"]).zfill(4), "%H%M"
                    )

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
