from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysKRSpider(FiveGuysAUSpider):
    name = "five_guys_kr"
    experience_key = "search-backend-kr"
    locale = (
        "en-KR"  # Using en because it has google attributes which gives lots of extra details (not present in kr-KR)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:kr"] = item["website"].replace("/en_kr/", "/")
        item["website"] = item["extras"]["website:kr"]
