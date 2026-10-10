import re
from json import loads
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AureliosPizzaUSSpider(SitemapSpider):
    name = "aurelios_pizza_us"
    item_attributes = {"brand": "Aurelio's Pizza", "brand_wikidata": "Q4822251"}
    allowed_domains = ["www.aureliospizza.com"]
    sitemap_urls = ["https://www.aureliospizza.com/wp-sitemap-posts-maplist-1.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Each location page embeds the same JSON the store-locator map uses,
        # which is the only place coordinates and the stable numeric store id
        # (in "cssClass", e.g. "loc-167") are available.
        params_match = re.search(r"var maplistFrontScriptParams = (\{.*?\});", response.text)
        if not params_match:
            return
        location = loads(loads(params_match.group(1))["location"])
        ref_match = re.search(r"loc-(\d+)", location.get("cssClass", ""))
        if not ref_match:
            return

        item = Feature()
        item["ref"] = ref_match.group(1)
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item["website"] = response.url
        item["branch"] = response.css("h5.red::text").get("").strip()
        # The address link's text is split into fragments by a preceding
        # <i> icon element, so all of its text nodes need joining.
        item["addr_full"] = " ".join(t.strip() for t in response.css("a.gray")[0].css("::text").getall() if t.strip())
        item["phone"] = response.css('a[href^="tel:"]::attr(href)').get("").removeprefix("tel:").strip()

        # Hours are split across a variable number of <p> tags (carry-out vs
        # dine-in), so all are combined; anything from "Buffet Hours" onward
        # is dropped since it is always a redundant subset of the main hours.
        hours_text = ""
        for para in response.xpath('//h5[contains(text(),"Hours")]/following-sibling::p'):
            text = " ".join(para.css("::text").getall())
            if buffet_match := re.search(r"buffet", text, re.I):
                hours_text += " " + text[: buffet_match.start()]
                break
            hours_text += " " + text
        if hours_text.strip():
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_text.replace("&amp;", "and").replace("&", "and"))
            if oh.as_opening_hours():
                item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)

        yield item
