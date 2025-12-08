from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysKWSpider(FiveGuysAUSpider):
    name = "five_guys_kw"
    experience_key = "search-backend-kw"
    locale = (
        "ar-KW"  # Using ar because it has google attributes which gives lots of extra details (not present in en-KW)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:ar"] = item["website"]
        item["extras"]["website:en"] = item["website"].replace("fiveguys.com.kw/", "fiveguys.com.kw/en_kw/")
