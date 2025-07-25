import html

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class IhgHotelsSpider(SitemapSpider, StructuredDataSpider):
    name = "ihg_hotels"
    allowed_domains = ["ihg.com"]
    sitemap_urls = ["https://www.ihg.com/bin/sitemapindex.xml"]
    sitemap_follow = ["en-US.hoteldetail"]
    sitemap_rules = [(r"/hotels/us/en/[-\w]+/[-\w]+/hoteldetail$", "parse")]
    wanted_types = ["Hotel"]
    json_parser = "chompjs"
    requires_proxy = True

    my_brands = {
        "armyhotels": ("Army Hotels", "Q16994722"),
        "avidhotels": ("avid Hotel", "Q60749907"),
        "candlewood": ("Candlewood Suites", "Q5032010"),
        "crowneplaza": ("Crowne Plaza", "Q2746220"),
        "evenhotels": ("EVEN Hotels", "Q5416522"),
        "holidayinn": ("Holiday Inn", "Q2717882"),
        "holidayinnclubvacations": ("Holiday Inn Club Vacations", "Q111485843"),
        "holidayinnexpress": ("Holiday Inn Express", "Q5880423"),
        "holidayinnresorts": ("Holiday Inn Resort", "Q111485210"),
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
        item["name"] = html.unescape(item["name"].strip())

        if (hotel_type := response.url.split("/")[3]) in self.my_brands:
            item["brand"], item["brand_wikidata"] = self.my_brands.get(hotel_type)

        apply_category(Categories.HOTEL, item)

        if item["country"] == r"${hotelInfo.address.country.name}":
            # Fix bad country values
            item["country"] = None

        yield item
