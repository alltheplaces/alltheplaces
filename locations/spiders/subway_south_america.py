from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.spiders.subway import SubwaySpider
from locations.structured_data_spider import StructuredDataSpider


class SubwaySouthAmericaSpider(CrawlSpider, StructuredDataSpider):
    name = "subway_south_america"
    item_attributes = SubwaySpider.item_attributes
    allowed_domains = ["restaurantes.subway.com", "subway.business.monster"]
    start_urls = ["https://restaurantes.subway.com"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@id="lojas"]'), callback="parse_sd", follow=True),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = response.xpath('//script[contains(text(), "var endereco_formatado")]/text()').re_first(
            r"endereco_formatado = \"(.*)\""
        )
        item["country"] = item["addr_full"].split("-")[-1].strip()
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["takeaway"] = "yes"
        yield item
