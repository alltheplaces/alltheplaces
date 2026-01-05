from scrapy.http import Request

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

FUEL_TYPES_MAPPING = {
    "euro 95": Fuel.OCTANE_95,
    "euro95": Fuel.OCTANE_95,
    "super 98": Fuel.OCTANE_98,
    "super98": Fuel.OCTANE_98,
    "diesel": Fuel.DIESEL,
    "adblue": Fuel.ADBLUE,
    "lpg": Fuel.LPG,
    "cng": Fuel.CNG,
    "hvo 100": Fuel.BIODIESEL,
    "petroleum": Fuel.KEROSENE,
}


class FietenNLSpider(WPStoreLocatorSpider):
    name = "fieten_nl"
    item_attributes = {"brand": "Fieten Olie", "brand_wikidata": "Q125968048"}
    allowed_domains = ["www.fieten.info"]
    iseadgg_countries_list = ["NL"]
    search_radius = 50
    max_results = 50

    def post_process_item(self, item, response, feature):
        item["ref"] = feature["id"]
        if item["street_address"]:
            item["street_address"] = item["street_address"].replace(",", "")
        item["website"] = feature.get("permalink")
        apply_category(Categories.FUEL_STATION, item)

        if item["website"]:
            yield Request(url=item["website"], callback=self.parse_fuel_types, meta={"item": item})
        else:
            yield item

    def parse_fuel_types(self, response):
        item = response.meta["item"]

        for fuel_div in response.xpath('//div[@class="station-price-content"]'):
            fuel_type = fuel_div.xpath('.//span[@class="fuel-text"]/text()').get()
            if fuel_type:
                fuel_type = fuel_type.strip().lower()
                if fuel_tag := FUEL_TYPES_MAPPING.get(fuel_type):
                    apply_yes_no(fuel_tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/fieten_nl/fuel_type/fail/{fuel_type}")

        yield item
