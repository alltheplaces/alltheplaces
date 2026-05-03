from typing import Any

from scrapy.http import JsonRequest

from locations.spiders.technopolis_bg import AsyncIterator, TechnopolisBGSpider


class PraktikerBGSpider(TechnopolisBGSpider):
    name = "praktiker_bg"
    item_attributes = {"brand": "Praktiker", "brand_wikidata": "Q110399491"}
    allowed_domains = ["praktiker.bg"]

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            "https://api.praktiker.bg/videoluxcommercewebservices/v2/praktiker/mapbox/customerpreferedstore",
            headers={"Origin": "https://www.technopolis.bg"},
        )
