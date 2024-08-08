from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class JcpenneySpider(CrawlSpider, StructuredDataSpider):
    name = "jcpenney"
    item_attributes = {
        "brand": "JCPenney",
        "brand_wikidata": "Q920037",
        "extras": Categories.SHOP_DEPARTMENT_STORE.value,
    }
    allowed_domains = ["jcpenney.com"]
    start_urls = ["https://jcpenney.com/locations/"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}$"), follow=True),
        Rule(
            LinkExtractor(allow=r"/locations/[-\w]{2}/[-\w]+/clothing-stores-[-\w]+.html$"),
            follow=True,
            callback="parse_sd",
        ),
    ]
    user_agent = BROWSER_DEFAULT
    wanted_types = ["DepartmentStore"]
    requires_proxy = True
