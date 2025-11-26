import asyncio

from playwright.async_api import Page
from playwright_captcha import CaptchaType, ClickSolver, FrameworkType
from scrapy import Spider
from scrapy.http import Request

from locations.playwright_spider import PlaywrightSpider


class CamoufoxSpider(PlaywrightSpider):
    @staticmethod
    async def click_solver(page: Page, request: Request, spider: Spider) -> None:
        """
        For a Playwright Page object returned from a Camoufox spider, detect
        if there is a click-solver captcha present to solve, then solve it
        automatically. See locations/middlewares/playwright_middleware.py for
        more description of what a Camoufox spider is.

        Click-solver captchas are solved by the user clicking on an object on
        the page. Implementations include:
          * Cloudflare Interstitial
          * Cloudflare Turnstile
        """
        if await page.title() == "Just a moment...":
            # Cloudflare Turnstile detected

            # Wait for a few seconds for the Cloudflare iframe to be
            # requested/rendered. Whilst playwright_captcha will enter a
            # polling loop waiting for a Cloudflare iframe to appear, it will
            # generate a noisy exception in doing so. This noise can be
            # avoided by waiting a few seconds to start the captcha solver.
            await asyncio.sleep(2)

            solver = ClickSolver(framework=FrameworkType.CAMOUFOX, page=page)
            await solver.prepare()

            if captcha_selector_indicating_success := getattr(spider, "captcha_selector_indicating_success"):
                # Preferred method for a spider to confirm that a click-solver
                # captcha has been successfully solved. The spider must set
                # attribute "captcha_selector_indicating_success" to a string
                # which is an XPath expression that will return one or more
                # elements from the page only if the captcha is successfully
                # solved.
                #
                # For example, this XPath expression could detect the real
                # website has been successfully loaded by checking text of a
                # h1 heading is the website's name.
                #  captcha_selector_indicating_success = '//h1[text()="ACME Inc"]'
                await solver.solve_captcha(
                    captcha_container=page,
                    captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE,
                    expected_content_selector=captcha_selector_indicating_success,
                )
            else:
                # Fallback (default) mechanism where playwright_captcha tries
                # to find a signal from the page after clicking that the
                # captcha is successfully solved. For example, maybe there is
                # a 1 second delay where "Success" is printed, before the page
                # redirects. This is generally unreliable as a method for
                # detecting successful solving for a click-solver captcha.
                await solver.solve_captcha(captcha_container=page, captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE)
