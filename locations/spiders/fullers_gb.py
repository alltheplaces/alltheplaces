from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class FullersGBSpider(CamoufoxSpider):
    name = "fullers_gb"
    item_attributes = {"brand": "Fuller's", "brand_wikidata": "Q5253950"}
    allowed_domains = ["fullers.co.uk"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "fetch"]
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            "https://www.fullers.co.uk/pubs/pub-finder",
            meta={
                "camoufox_page_methods": [
                    PageMethod(
                        "evaluate",
                        """async () => {
                                    const BATCH = 30;
                                    const fetchJson = async (url, init) => {
                                        const response = await fetch(url, init);
                                        if (!response.ok) throw new Error(url + " returned HTTP " + response.status);
                                        return await response.json();
                                    };
                                    const feedPage = (page) => fetchJson("/api/main/pubs/feed", {
                                        method: "POST",
                                        headers: {"Content-Type": "application/x-www-form-urlencoded"},
                                        body: "pageNumber=" + page + "&latitude=0&longitude=0&area=",
                                    });

                                    const firstPage = await feedPage(1);
                                    const remaining = [];
                                    for (let page = 2; page <= firstPage.totalPages; page++) remaining.push(feedPage(page));

                                    const pubs = [...firstPage.items];
                                    for (const feed of await Promise.all(remaining)) pubs.push(...feed.items);

                                    for (let i = 0; i < pubs.length; i += BATCH) {
                                        await Promise.all(pubs.slice(i, i + BATCH).map(async (pub) => {
                                            pub.information = await fetchJson("/api/main/pubs/information?pubId=" + pub.pubId);
                                        }));
                                    }
                                    return pubs;
                                }""",
                    )
                ]
            },
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        for pub in response.meta["camoufox_page_methods"][0].result:
            information = pub["information"]

            item = Feature()
            item["ref"] = pub["pubId"]
            item["addr_full"] = pub["subTitle"]
            item["lat"] = information["googleMaps"]["coords"]["lat"]
            item["lon"] = information["googleMaps"]["coords"]["lng"]
            item["phone"] = information["socials"]["phoneNumber"]["value"]
            item["email"] = information["socials"]["email"]["value"]
            item["website"] = information["socials"]["website"]["link"]

            # Titles append the locality, eg "The Willow, Bourton-on-the-Water". Split from the
            # right as some pub names contain a comma, eg "The Lock, Stock & Barrel, Newbury".
            item["branch"] = pub["title"].rsplit(",", 1)[0]

            item["opening_hours"] = OpeningHours()
            for day in (information["timesData"] or {}).get("openingTimes", []):
                for times in day["values"]:
                    if times == "Closed":
                        item["opening_hours"].set_closed(day["label"])
                    else:
                        item["opening_hours"].add_range(day["label"], *times.split("-"))

            apply_category(Categories.PUB, item)
            yield item
