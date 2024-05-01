from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class IHGHotelsSpider(SitemapSpider, StructuredDataSpider):
    name = "ihg_hotels"
    allowed_domains = ["ihg.com"]
    sitemap_urls = ["https://www.ihg.com/bin/sitemapindex.xml"]
    sitemap_follow = ["en.hoteldetail"]
    sitemap_rules = [(r"/hotels/us/en/[-\w]+/[-\w]+/hoteldetail$", "parse")]
    wanted_types = ["Hotel"]
    json_parser = "chompjs"
    requires_proxy = True

    my_brands = {
        "armyhotels": ("Army Hotels", "Q16994722"),
        "avidhotels": ("Avid Hotels", "Q60749907"),
        "candlewood": ("Candlewood Suites", "Q5032010"),
        "crowneplaza": ("Crowne Plaza", "Q2746220"),
        "evenhotels": ("Even Hotels", "Q5416522"),
        "holidayinn": ("Holiday Inn", "Q2717882"),
        "holidayinnclubvacations": (None, None),
        "holidayinnexpress": ("Holiday Inn Express", "Q5880423"),
        "holidayinnresorts": (None, None),
        "hotelindigo": ("Hotel Indigo", "Q5911596"),
        "intercontinental": ("InterContinental", "Q1825730"),
        "kimptonhotels": ("Kimpton", "Q6410248"),
        "regent": ("Regent", "Q3250375"),
        "spnd": (None, None),
        "staybridge": ("Staybridge Suites", "Q7605116"),
        "vignettecollection": (None, None),
        "voco": ("Voco Hotels", "Q60750454"),
    }

    def parse(self, response, **kwargs):
        if response.url.endswith("hoteldetail"):
            yield from self.parse_sd(response)

    def post_process_item(self, item, response, ld_data):
        if not item.get("street_address"):
            return
        item["name"] = item["name"].strip("\n").strip("\t")

        if (hotel_type := response.url.split("/")[3]) in self.my_brands:
            item["brand"], item["brand_wikidata"] = self.my_brands.get(hotel_type)

        apply_category(Categories.HOTEL, item)

        yield item
