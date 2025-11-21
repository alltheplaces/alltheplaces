from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BasicFitFRSpider(CrawlSpider, StructuredDataSpider):
    name = "basic_fit_fr"
    item_attributes = {"brand": "Basic-Fit", "brand_wikidata": "Q40165577"}
    allowed_domains = ["www.basic-fit.com"]
    start_urls = ["https://www.basic-fit.com/fr-fr/salles-de-sport"]
    rules = [
        Rule(LinkExtractor(allow=r"https://www.basic-fit.com/fr-fr/salles-de-sport")),
        Rule(LinkExtractor(allow=r"https://www.basic-fit.com/fr-fr/clubs/.*.html"), callback="parse_sd"),
    ]
    custom_settings = {"DOWNLOAD_DELAY": 2}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Salle de sport ")

        if hours_elements_text := response.css(".club-opening-hours").css("::text").getall():
            hours_text = " ".join([text.strip() for text in hours_elements_text if text.strip()])
            if hours_text:
                if "24H/24" in hours_text or "24h/24" in hours_text:
                    item["opening_hours"] = "24/7"
                else:
                    hours_text = (
                        hours_text.replace("Du ", "")
                        .replace(" au ", "-")
                        .replace(" & ", ",")
                        .replace(" et ", ",")
                        .replace("de ", "")
                        .replace(" à ", "-")
                        .replace("h", ":")
                        .replace(" : ", ": ")
                    )
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_FR)

        apply_category(Categories.GYM, item)

        yield item
