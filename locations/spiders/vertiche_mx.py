from geonamescache import GeonamesCache
from scrapy import Request
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories
from locations.hours import DAYS_ES
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VerticheMXSpider(WPStoreLocatorSpider):
    name = "vertiche_mx"
    item_attributes = {"brand": "Vertiche", "brand_wikidata": "Q113215945", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["vertiche.mx"]
    start_urls = ["https://vertiche.mx/nuestras-tiendas/"]
    max_results = 25
    search_radius = 11
    days = DAYS_ES
    time_format = "%I:%M %p"

    def start_requests(self):
        # The maximum search radius for this WPStoreLocator
        # implementation is seemingly very small. The store locator
        # locator page offers a drop-down list of cities which can
        # be searched for stores. These city names are converted to
        # search coordinates using Google Maps APIs. Instead, we use
        # geonamescache to perform an offline lookup of city names
        # to coordinates.
        # NOTE: geonamescache is very CPU intensive to search. The
        #       performance of this library is quite poor.
        yield Request(url=self.start_urls[0], callback=self.parse_cities_list)

    def parse_cities_list(self, response):
        # <select> tag is self-closed so when parsing, there are no
        # <option> tags found. To fix this HTML error, find all
        # <option> tags within a higher <div> tag.
        for city_key in response.xpath('//div[@class="wpsl-input"]//option/text()').getall():
            if not city_key or city_key == "-":
                continue
            city_name = (
                unidecode(city_key).split(",", 1)[0].replace("Cd. ", "Ciudad ").replace("Cd ", "Ciudad ").strip()
            )
            manual_replacements = {
                "Cabos San Lucas": "Cabo San Lucas",
                "Valle de Chalco": "Xico",
                "Zapotlan El Grande": "Ciudad Guzman",
                "Zihuatanejo de Azueta": "Ixtapa-Zihuatanejo",
            }
            if city_name in manual_replacements.keys():
                city_name = manual_replacements[city_name]
            gc = GeonamesCache(min_city_population=500)
            matched_cities = gc.search_cities(city_name, contains_search=False)
            mexican_cities = list(filter(lambda x: x["countrycode"] == "MX", matched_cities))
            if len(mexican_cities) == 0:
                self.logger.warning(
                    f"Coordinates could not be looked up in geonamescache for Mexican city: {city_name}. Locations in this city will not be returned."
                )
                continue
            for mexican_city in mexican_cities:
                lat = mexican_city["latitude"]
                lon = mexican_city["longitude"]
                yield JsonRequest(
                    url=f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                )

    def parse_item(self, item, location):
        item.pop("address", None)
        yield item
