from urllib.parse import urljoin

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider

ATTRIBUTES_MAP = {
    "Bulk DEF": None,
    "Check Cashing": None,
    "Compressed Air": Extras.COMPRESSED_AIR,
    "Diesel": Fuel.DIESEL,
    "Drive Thru": Extras.DRIVE_THROUGH,
    "E85 Gas": Fuel.E85,
    "EV Charging": Fuel.ELECTRIC,
    "Ethanol Free": Fuel.ETHANOL_FREE,
    "Free WiFi": Extras.WIFI,
    "Fried Chicken": "food",
    "Gaming Machines": None,
    "High Flow Diesel Lanes": "hgv",
    "Mid-grade 89": Fuel.OCTANE_89,
    "Pizza": "food",
    "Premium 93": Fuel.OCTANE_93,
    "Regular 87": Fuel.OCTANE_87,
    "Reserved Truck Parking": None,
    "Seating Area": None,
    "Self Checkout": Extras.SELF_CHECKOUT,
    "Swirl World": None,
    "Truck Merchandise": None,
    "Truck Parking": None,
}


class RaceTracUSSpider(SitemapSpider, StructuredDataSpider):
    name = "race_trac_us"
    item_attributes = {"brand": "RaceTrac", "brand_wikidata": "Q735942", "nsi_id": "N/A"}
    allowed_domains = ["www.racetrac.com"]
    sitemap_urls = ["https://www.racetrac.com/robots.txt"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["GasStation"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].startswith("/"):
                entry["loc"] = urljoin("https://www.racetrac.com/", entry["loc"])
            yield entry

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["url"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.FUEL_STATION, item)

        for amenity in response.xpath('//li[@class="amCol"]/span[@class="displayName"]/text()').getall():
            if attribute := ATTRIBUTES_MAP.get(amenity):
                apply_yes_no(attribute, item, True)
            else:
                self.crawler.stats.inc_value("atp/racetrac_us/unmapped_attribute/{}".format(amenity))

        yield item
