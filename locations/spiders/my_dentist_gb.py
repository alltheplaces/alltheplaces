from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class MyDentistGBSpider(CrawlSpider, StructuredDataSpider):
    MYDENTIST = {"brand": "My Dentist", "brand_wikidata": "Q65118035", "extras": Categories.DENTIST.value}

    name = "my_dentist_gb"
    allowed_domains = ["mydentist.co.uk"]
    start_urls = ["https://www.mydentist.co.uk/dentists/practices/"]
    rules = [
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+)(\/[-\w]+)?(\/[-\w]+)?$",
            ),
        ),
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+\/[-\w]+\/[-\w]+\/[-\w]+)$",
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//input[@name="Latitude"]/@value').get()
        item["lon"] = response.xpath('//input[@name="Longitude"]/@value').get()

        # City can come back as eg ["Penistone", "Sheffield"] - put the locality on the end of street address
        if "city" in item and isinstance(item["city"], list):
            item["street_address"] = clean_address([item["street_address"]] + item["city"][:-1])
            item["city"] = item["city"][-1]

        if item["name"] is not None and (
            item["name"].startswith("mydentist") or item["name"].startswith("{my}dentist")
        ):
            item.update(self.MYDENTIST)
            item["name"] = "{my}dentist"

        if isinstance(item.get("email"), list):
            item["email"] = ", ".join(item["email"])

        yield item
