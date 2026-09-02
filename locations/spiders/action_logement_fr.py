from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ActionLogementFRSpider(CrawlSpider, StructuredDataSpider):
    name = "action_logement_fr"
    item_attributes = {
        "brand": "Action Logement",
        "brand_wikidata": "Q98755057",
    }
    allowed_domains = ["www.actionlogement.fr"]
    start_urls = ["https://www.actionlogement.fr/implantations"]
    rules = [
        Rule(LinkExtractor(allow=r"https://www.actionlogement.fr/"), follow=False, callback="parse_sd"),
    ]

    drop_attributes = ["twitter"]

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)

        item["lat"] = response.css("a#open-itinerary::attr(data-lat)").get()
        item["lon"] = response.css("a#open-itinerary::attr(data-lon)").get()

        item["branch"] = (item.pop("name", "") or "").removeprefix("Agence Action Logement ")

        yield item
