from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BarbequesGaloreAU(CrawlSpider, StructuredDataSpider):
    name = "barbeques_galore_au"
    item_attributes = {"brand": "Barbeques Galore", "brand_wikidata": "Q4859570"}
    allowed_domains = ["www.barbequesgalore.com.au"]
    start_urls = ["https://www.barbequesgalore.com.au/stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r".*/stores/(?:act|nsw|nt|qld|sa|tas|vic|wa)/all-stores-in.*"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r".*/stores/[a-z\-]+"),
            callback="parse_sd",
            follow=False,
        ),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("facebook")
        item["ref"] = response.xpath('//div[contains(@class, "store-details")]/@data-store-id').extract_first()
        item["opening_hours"] = OpeningHours()
        hours_raw = (
            " ".join(
                response.xpath(
                    '//div[contains(@class, "open-section")][1]/div[contains(@class, "open-hour")]/span/text()'
                ).extract()
            )
            .replace("Closed", "0:00am - 0:00am")
            .replace("-", "")
            .replace(")", "")
            .replace("(", "")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1] == "0:00am" and day[2] == "0:00am":
                continue
            item["opening_hours"].add_range(DAYS_EN[day[0]], day[1].upper(), day[2].upper(), "%I:%M%p")
        yield item
