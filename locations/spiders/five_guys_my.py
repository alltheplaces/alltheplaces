from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysMYSpider(FiveGuysAUSpider):
    name = "five_guys_my"
    experience_key = "search-backend-my"
    locale = (
        "en"  # Using en because it has google attributes which gives lots of extra details (not present in zh-Hans)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:zh"] = item["website"].replace("/en/", "/")
        item["website"] = item["extras"]["website:zh"]
