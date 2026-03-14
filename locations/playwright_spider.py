from playwright.async_api import Response as PlaywrightResponse
from scrapy import Spider


class PlaywrightSpider(Spider):
    _last_scrapy_request_url: str | None = None
    _last_observed_xml_document: str | None = None

    async def detect_xml_document_from_playwright_response(self, response: PlaywrightResponse) -> None:
        """
        Refer to middlewares/playwright_middleware.py for more information on
        the purpose of this function.
        """
        if response.url == getattr(self, "_last_scrapy_request_url"):
            response_text = await response.text()
            if response_text.strip().startswith("<?xml"):
                if "<?xml-stylesheet" in response_text:
                    # Only XML documents with an XSL stylesheet need to have
                    # their original XML document temporarily captured by the
                    # spider, allowing the browser's transformation of the XML
                    # document into a HTML document (or other XML
                    # representation) to be ignored.
                    setattr(self, "_last_observed_xml_document", response_text)
