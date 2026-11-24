from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response, TextResponse

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class StephanePlazaImmobilierFRSpider(Spider):
    name = "stephane_plaza_immobilier_fr"
    item_attributes = {"brand_wikidata": "Q97368097", "name": "Stéphane Plaza Immobilier"}
    allowed_domains = ["www.stephaneplazaimmobilier.com"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    # The API answers 403 without a session cookie (set by /agences/), the AJAX header and the Fetch Metadata headers of a browser.
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.stephaneplazaimmobilier.com/agences/", callback=self.parse_session)

    def parse_session(self, response: Response) -> Any:
        yield Request(url="https://www.stephaneplazaimmobilier.com/agencies/search?page=1", headers=self.headers)

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        agencies = response.json()["agencies"]
        if agencies["next_page_url"]:
            yield Request(url=agencies["next_page_url"], headers=self.headers)
        for agency in agencies["data"]:
            if agency["real_estate_agency_prochainement"] == "1":  # not opened yet
                continue
            item = DictParser.parse({k.removeprefix("real_estate_agency_"): v for k, v in agency.items()})
            item["street_address"] = item.pop("addr_full", None)
            if (name := item.pop("name")) and name.lower().startswith("stéphane plaza immobilier "):
                item["branch"] = name[len("Stéphane Plaza Immobilier ") :]
            yield item
