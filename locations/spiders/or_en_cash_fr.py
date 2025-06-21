from typing import Iterable

from chompjs import parse_js_object
from scrapy import Selector, Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class OrEnCashFRSpider(Spider):
    name = "or_en_cash_fr"
    item_attributes = {"brand": "Or en Cash", "brand_wikidata": "Q115088395"}
    allowed_domains = ["www.orencash.fr"]
    start_urls = ["https://www.orencash.fr/wp-content/themes/orencash/js/markers.php"]

    def parse(self, response: Response) -> Iterable[Request]:
        markers_js = "[" + ", ".join(map(lambda x: x.split(");", 1)[0], response.text.split("a.push(")[1:])) + "]"
        markers = parse_js_object(markers_js)
        for marker in markers:
            popup_html = Selector(text="<div>" + marker["name"] + "</div>")
            properties = {
                "ref": popup_html.xpath("//div/a/@href").get(),
                "lat": marker["lat"],
                "lon": marker["lng"],
                "branch": popup_html.xpath("//div/h3/text()").get().split(" – Rachat", 1)[0].split(" – Achat", 1)[0],
                "addr_full": merge_address_lines(popup_html.xpath("//div/text()").getall()),
                "website": popup_html.xpath("//div/a/@href").get(),
            }
            apply_category(Categories.SHOP_GOLD_BUYER, properties)
            # Don't bother following the location-specific website URL as it
            # only contains a location-specific phone number Facebook page.
            # However, the website is VERY aggressive with rate limiting, so
            # it's not worth the hassle to obtain these low value fields.
            # Location-specific websites may occassionally contain some
            # opening hours information, but the significant majority of the
            # time there is just a comment asking people to click through to
            # Google Maps and/or Facebook for opening hours information.
            yield Feature(**properties)
