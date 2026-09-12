import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TacoBillAUSpider(Spider):
    name = "taco_bill_au"
    item_attributes = {"brand": "Taco Bill", "brand_wikidata": "Q104528301", "name": "Taco Bill", "country": "AU"}
    allowed_domains = ["tacobill.com.au"]
    start_urls = ["https://www.tacobill.com.au/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The site's nav "LOCATIONS" dropdown is the only place that reliably lists just the
        # store pages (other page links share the same nav markup on every page).
        for link in response.xpath('//button[@aria-label="More LOCATIONS pages"]/following-sibling::ul[1]//a'):
            branch = link.xpath("normalize-space(./text())").get()
            yield response.follow(link.xpath("./@href").get(), callback=self.parse_store, cb_kwargs={"branch": branch})

    def parse_store(self, response: Response, branch: str) -> Iterable[Feature]:
        heading = response.xpath('//p[.//text()[normalize-space()="Address"]]')
        if not heading:
            return

        # Each store page renders its details as a flat sequence of <p> paragraphs (Address,
        # street lines, Contact, phone, hours, ...); a span can split mid-word/mid-number, so
        # text nodes within a paragraph are joined with no separator rather than a space.
        lines = []
        for p in heading.xpath("..").xpath("./p"):
            text = "".join(p.xpath(".//text()").getall()).replace("​", "").strip()
            if text:
                lines.append(text)

        if "Contact" not in lines:
            return
        contact_index = lines.index("Contact")

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = branch
        item["addr_full"] = ", ".join(lines[1:contact_index])
        if m := re.search(r"\b([A-Z]{2,3})\s+(\d{4})$", item["addr_full"]):
            item["state"], item["postcode"] = m.groups()
        if len(lines) > contact_index + 1:
            item["phone"] = lines[contact_index + 1].removeprefix("T.").strip()
        item["website"] = response.url

        apply_category(Categories.RESTAURANT, item)
        yield item
