import re
from urllib.parse import urlparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# The one locator serves two brands: the Georgia restaurants keep the Johnny's name,
# while those in other states redirect to the Johnny Brusco's site.
BRANDS = {
    "johnnyspizza.com": "Johnny's New York Style Pizza",
    "johnnybruscos.com": "Johnny Brusco's New York Style Pizza",
}


class JohnnysNewYorkStylePizzaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "johnnys_new_york_style_pizza_us"
    sitemap_urls = ["https://johnnyspizza.com/location-sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        # Two pages publish an empty name, where the title still leads with the branch.
        item["branch"] = item.pop("name", None) or response.xpath("//title/text()").re_first(r"\s*([^|]+?)\s*\|")

        host = urlparse(response.url).netloc.removeprefix("www.")
        if not (brand := BRANDS.get(host)):
            self.logger.warning(f"Unrecognised brand host {host!r} on {response.url}")
            return
        item["brand"] = brand

        # The structured data leaves postalCode empty on every page. The address
        # rendered beside the map link usually ends with the postcode, and where it
        # does not, the page echoes its own location record as a debug dump that
        # states one. That dump is a fault rather than a feature, so it is only read
        # as a fallback and only for the postcode.
        # Most pages link the address to a Google place by its id, a few by the
        # address itself, so the link is matched on being a map link of either form.
        link = response.xpath(
            '//a[contains(@href, "google.com/maps") or contains(@href, "maps.google.com")]'
            '[re:test(normalize-space(.), "^\\d+\\s")]'
        )
        address = link.xpath("normalize-space(.)").get("")
        if postcode := re.search(r"(\d{5}(?:-\d{4})?)\s*$", address):
            item["postcode"] = postcode.group(1)
        elif postcode := re.search(r"\[postalCode\]\s*=>\s*(\d{5}(?:-\d{4})?)", response.text):
            item["postcode"] = postcode.group(1)

        if place_id := link.xpath("@href").re_first(r"place_id:([^&'\"]+)"):
            item["extras"]["ref:google:place_id"] = place_id

        # Each restaurant has its own Facebook page, but the one Twitter account is
        # the brand's, repeated on all of its locations.
        item["twitter"] = None

        # No coordinates are published: the only pair on the page sits in an HTML
        # comment and is the same default on every location.
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
