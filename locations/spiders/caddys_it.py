from locations.categories import Categories
from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class CaddysITSpider(JSONBlobSpider):
    name = "caddys_it"
    item_attributes = {
        "brand": "Caddy's",
        "brand_wikidata": "Q108604630",
        "country": "IT",
        "extras": Categories.SHOP_CHEMIST.value,
    }
    allowed_domains = ["www.caddys.it"]
    start_urls = [
        "https://www.caddys.it/on/demandware.store/Sites-Caddys-Site/it_IT/Stores-FindStores?radius=2500&lat=25.56009518531322&long=6.903786000000025&selectedFilters="
    ]
    locations_key = "stores"
    # no url per-store is available from the API
    # but a sitemap would be available to get those URLs, from which we would need to scrape info from HTML
    # pipenv run scrapy sitemap --pages https://www.caddys.it/sitemap-negozi.xml | awk '/negozi\/[^\/]+\/[^\/]+$/ { print $0 }'

    def pre_process_data(self, location):
        # some stores are defined with wrong country code (DE/US), even if they're all in Italy
        if "countryCode" in location:
            del location["countryCode"]
        # stateCode is unuseful, mostly 'Italia' or empty
        if "stateCode" in location:
            del location["stateCode"]

    def post_process_item(self, item, response, location):
        # opening hours are written with just hours split by | or /, sometimes sunday is omitted when closed
        for day_split, delimiters in [("|", "-/"), ("/", "-")]:
            if len(location.get("storeHours", "").split(day_split)) >= 6:
                oph = OpeningHours()
                for day, hours in zip(DAYS_IT, f"{location['storeHours']} {day_split} CHIUSO".split(day_split)):
                    oph.add_ranges_from_string(
                        f"{day} {hours}",
                        days=DAYS_IT,
                        closed=CLOSED_IT,
                    )
                item["opening_hours"] = oph
                break
        item["state"] = location["provincia"]
        if location.get("parafarmacia", False):
            item["extras"].update(Categories.PHARMACY.value)
            item["extras"]["dispensing"] = "no"
        yield item
