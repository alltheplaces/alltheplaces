from chompjs import parse_js_object
from scrapy import Request

from locations.categories import Categories
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

OLD_MUTUAL_BRANDS = {
    "Old Mutual Insure": {
        "brand": "Old Mutual Insure",
        "brand_wikidata": "Q289704",
        "extras": Categories.OFFICE_INSURANCE.value,
    },
    "Old Mutual Finance": {
        "brand": "Old Mutual Finance",
        "brand_wikidata": "Q289704",
        "extras": Categories.OFFICE_FINANCIAL.value,
    },
    "Old Mutual ATM": {"brand": "Old Mutual", "brand_wikidata": "Q289704", "extras": Categories.ATM.value},
}


class OldMutualZASpider(JSONBlobSpider):
    name = "old_mutual_za"
    start_urls = ["https://www.oldmutual.co.za/about/branch-locator/"]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_js)

    def fetch_js(self, response):
        yield Request(
            url="https://www.oldmutual.co.za"
            + response.xpath('.//script[contains(@src, "/page--src--templates--branch-locator-page-vue")]/@src').get(),
            callback=self.parse,
        )

    def extract_json(self, response):
        data = parse_js_object(response.text[response.text.index("allBranch:{") :])["edges"]
        return [i["node"] for i in data]

    def post_process_item(self, item, response, location):
        if (attributes := OLD_MUTUAL_BRANDS.get(location["brand"])) is not None:
            item.update(attributes)
        else:
            self.logger.warning(f"Unknown brand: {location['brand']}")

        # Some locations do not have the full brand in their name
        item["branch"] = (
            item.pop("name").replace(item.get("brand"), "").replace("Old Mutual", "").replace("ATM", "").strip()
        )
        item["street_address"] = clean_address([location.get("address_line_1"), location.get("address_line_2")])
        item.pop("website")  # Websites are generic
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            open = location.get(day.lower()).get("open")
            close = location.get(day.lower()).get("close")
            if open == "" and close == "":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, open, close, time_format="%H:%M:%S")
        yield item
