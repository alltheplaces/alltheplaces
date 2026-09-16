import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RuthsChrisSteakHouseUSSpider(Spider):
    name = "ruths_chris_steak_house_us"
    item_attributes = {"brand": "Ruth's Chris Steak House", "brand_wikidata": "Q7382829"}
    allowed_domains = ["www.ruthschris.com", "r.jina.ai"]
    start_urls = ["https://www.ruthschris.com/locations-sitemap.xml"]
    reader_headers = {"X-Return-Format": "markdown"}
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_USER_AGENT": "ChatGPT-User",
        "USER_AGENT": "Mozilla/5.0",
    }

    def parse(self, response: Response, **kwargs) -> Iterable[Request]:
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            yield Request(
                url=f"https://r.jina.ai/http://{url}",
                headers=self.reader_headers,
                callback=self.parse_location,
                meta={"official_url": url},
            )

    def parse_location(self, response: Response, **kwargs) -> Iterable[Feature]:
        official_url = response.meta["official_url"]

        item = Feature()
        item["ref"] = official_url.rstrip("/").rsplit("/", 1)[-1]
        item["name"] = "Ruth's Chris Steak House"
        item["branch"] = self.parse_branch(response, official_url)
        item["website"] = official_url

        if coordinates := re.search(r"pin-l-shop\+BE2F37\((-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\)", response.text):
            item["lon"], item["lat"] = coordinates.groups()

        if phone := re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", response.text):
            item["phone"] = phone.group()

        address = self.parse_address(response, item["branch"])
        if not address or not re.fullmatch(r"\d{5}(?:-\d{4})?", address["postcode"]):
            return

        item.update(address)
        item["extras"]["cuisine"] = "american;steak_house"
        apply_category(Categories.RESTAURANT, item)
        yield item

    @staticmethod
    def parse_branch(response: Response, official_url: str) -> str:
        if title := response.xpath("//title/text()").get():
            if " | Locations | " in title and (branch := title.split("|", 1)[0].strip()):
                return branch

        if branch := re.search(r"Add to Favorites\s*\n\s*([^\n]+)\s*\n\s*\[Explore", response.text):
            return branch.group(1).strip()

        return official_url.rstrip("/").rsplit("/", 2)[-2].replace("-", " ").title()

    @staticmethod
    def parse_address(response: Response, branch: str) -> dict | None:
        lines = [
            line.strip()
            for text in response.xpath('//a[contains(@href, "google.com/maps")]//text()').getall()
            for line in text.splitlines()
            if line.strip()
        ]
        if len(lines) >= 2 and (place := re.match(r"^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", lines[-1])):
            return {
                "street_address": merge_address_lines(lines[:-1]),
                "city": place.group(1),
                "state": place.group(2),
                "postcode": place.group(3),
                "country": "US",
            }

        address_text = merge_address_lines(lines)
        if not address_text and (
            address := re.search(
                r"\[([^\]\n]+(?:,?\s+[A-Z]{2})\s+\d{5}(?:-\d{4})?)\]\(https://www\.google\.com/maps\?q=",
                response.text,
            )
        ):
            address_text = re.sub(r"\s+", " ", address.group(1)).strip()

        if not (place := re.match(r"^(.*?)\s*,?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", address_text)):
            return None

        street_address, city = RuthsChrisSteakHouseUSSpider.split_street_city(place.group(1), branch)
        return {
            "street_address": street_address,
            "city": city,
            "state": place.group(2),
            "postcode": place.group(3),
            "country": "US",
        }

    @staticmethod
    def split_street_city(street_city: str, branch: str) -> tuple[str, str | None]:
        candidates = [branch]
        words = branch.split()
        candidates.extend(" ".join(words[i:]) for i in range(1, len(words)))
        if branch.startswith("St "):
            candidates.append(branch.replace("St ", "St. ", 1))

        for city in sorted(set(candidates), key=len, reverse=True):
            if street_city.lower().replace(".", "").endswith(city.lower().replace(".", "")):
                street_address = re.sub(rf"\s+{re.escape(city)}$", "", street_city, flags=re.I).strip()
                if street_address != street_city:
                    return street_address, city

        parts = street_city.rsplit(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]

        return street_city, None
