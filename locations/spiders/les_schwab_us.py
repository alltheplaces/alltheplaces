import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


# The shop webpages do have structured data, but they do not have coordinates,
# so we need to use a different method.
class LesSchwabUSSpider(SitemapSpider):
    name = "les_schwab_us"
    item_attributes = {
        "brand": "Les Schwab Tire Center",
        "brand_wikidata": "Q6529977",
    }
    sitemap_urls = ["https://www.lesschwab.com/sitemap-custom-stores.xml"]
    sitemap_rules = [
        (r"^https://www.lesschwab.com/stores/[a-z]{2}$", "parse"),
    ]

    def parse(self, response):
        for location in json.loads(response.xpath("//@data-locations").get()):
            item = DictParser.parse(location)
            item["name"], item["branch"] = item["name"].split(" - ")
            el = response.xpath(f"//div[@data-store-map-id={location['id']}]")
            item["website"] = response.urljoin(el.css(".js-store-detail-url::attr(href)").get())
            _, _, item["street_address"] = el.css(".storeDetails__streetName::text").get().partition(".")
            _, _, item["addr_full"] = merge_address_lines(el.xpath(".//address//text()").getall()).partition(".")

            oh = OpeningHours()
            for line in el.xpath(".//h6/../div//text()").getall():
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh

            yield item
