import string

from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class FnbBanksZASpider(Spider):
    # download_delay = 0.2
    name = "fnb_banks_za"
    item_attributes = {"brand": "FNB", "brand_wikidata": "Q3072956", "extras": Categories.BANK.value}

    def start_requests(self):
        # Search claims to accept search by province, in practice this returns barely any results
        # Single letter searches return no results, so doing this instead
        letter_pairs = [i + j for i in string.ascii_lowercase for j in string.ascii_lowercase]
        for pair in letter_pairs:
            yield Request(
                url="https://www.fnb.co.za/Controller?nav=locators.BranchLocatorSearch",
                body="nav=locators.BranchLocatorSearch&branchName=" + pair,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST",
            )

    def parse(self, response):
        onclicks = response.xpath('.//a[@class="link fontTurq searchResult       "]/@onclick').getall()
        links = [onclick.split("(event,'")[1].split("');")[0] for onclick in onclicks]

        for link in links:
            yield Request(url="https://www.fnb.co.za" + link, callback=self.parse_item)

    def parse_item(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        properties = {
            "branch": response.xpath(".//h2/text()").get().strip(),
            "lon": response.xpath('.//p[@class="  fontGrey   linePadding "]/text()').getall()[1].strip(),
            "lat": response.xpath('.//p[@class="  fontGrey    "]/text()').getall()[1].strip(),
            "ref": response.request.url.replace(
                "https://www.fnb.co.za/Controller?nav=locators.BranchLocatorSearch&costCentreCode=", ""
            ).replace("&details=true", ""),
            "addr_full": response.xpath('.//p[@class="      "]/strong/text()').get().strip(),
            "email": response.xpath('.//p[@class="     linePadding "]/.//a[contains(@href, "@")]/@href').get(),
            "phone": response.xpath('.//p[@class="     linePadding "]/strong/text()').get().strip(),
        }

        if properties["email"] == "info@fnb.co.za":
            properties.pop("email")
        if not (properties["phone"][0] == "(" or properties["phone"][0] == "0"):
            properties.pop("phone")
        # Generic telephone banking number
        if properties["phone"].replace(" ", "").replace("(", "").replace(")", "") == "0875759404":
            properties.pop("phone")

        wifi = (
            response.xpath('.//div[@class="readOut"]/label[contains(text(), "Wifi")]/.././/strong/text()').get().strip()
        )
        apply_yes_no(Extras.WIFI, properties, wifi == "Yes", False)

        oh = OpeningHours()
        for day in DAYS_FULL:
            times = (
                response.xpath('.//div[@class="readOut"]/label[contains(text(), "' + day + '")]/.././/strong/text()')
                .get()
                .strip()
            )
            if times.lower() == "closed":
                oh.set_closed(day)
            else:
                oh.add_ranges_from_string(f"{day} {times}")
        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
