import chompjs
from scrapy.http import JsonRequest, Request

from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class UciCinemasItSpider(JSONBlobSpider):
    name = "uci_cinemas_it"
    item_attributes = {
        "brand": "UCI Cinemas",
        "brand_wikidata": "Q521922",
        "extras": Categories.CINEMA.value,
    }
    start_urls = ["https://www.ucicinemas.it/rest/v3/cinemas/"]
    http_page = "https://www.ucicinemas.it/cinema/"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    headers = {
        "Authorization": "Bearer SkAkzoScIbhb3uNcGdk8UL0XMIbvs5",
    }
    id_to_website = dict()
    requires_proxy = "IT"  # Cloudflare bot protection used

    def start_requests(self):
        yield Request(self.http_page, callback=self.map_websites, dont_filter=True)

    def map_websites(self, response):
        links = response.css(".autocomplete-datasource .cinema a")
        for link in links:
            self.id_to_website[link.attrib["data-cr-id"]] = f"https://www.ucicinemas.it{link.attrib['href']}"
        yield JsonRequest(self.start_urls[0], headers=self.headers)

    def pre_process_data(self, location):
        location["id"] = location.pop("source_id")
        location["website"] = self.id_to_website.get(str(location["id"]))

    def post_process_item(self, item, response, location):
        item["branch"] = item["name"]
        item["name"] = item["name"].split("|")[0].strip()
        if url := item.get("website"):
            yield Request(url, cb_kwargs={"item": item}, callback=self.extract_address)
        else:
            yield item

    def extract_address(self, response, item):
        obj = chompjs.parse_js_object(
            response.xpath("//script[@type=$ldjson]/text()", ldjson="application/ld+json").get()
        )
        item["addr_full"] = obj["address"]["streetAddress"]
        item["postcode"] = obj["address"]["postalCode"]
        item["city"] = obj["address"]["addressLocality"]
        yield item
