from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PitaPitCASpider(SitemapSpider, StructuredDataSpider):
    name = "pita_pit_ca"
    item_attributes = {
        "brand_wikidata": "Q7757289",
        "brand": "Pita Pit",
    }
    allowed_domains = [
        "pitapit.ca",
    ]

    sitemap_urls = ["https://pitapit.ca/sitemap_index.xml"]
    sitemap_rules = [(r"https://pitapit.ca/restaurants/\w+/$", "parse_sd")]
    wanted_types = ["Restaurant"]


    def post_process_item(self, item, response, ld_data, **kwargs):
        if "| " in name:
            item["name"] = item["name"].split(" | ")[0].replace("Health Food Restaurant at ", "")

        yield item
