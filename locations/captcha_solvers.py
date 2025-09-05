import asyncio

from playwright.async_api import Page
from playwright_captcha import CaptchaType, ClickSolver, FrameworkType
from scrapy import Spider
from scrapy.http import Request


async def cloudflare_turnstile_solver(page: Page, request: Request, spider: Spider) -> None:
    """
    Click-solver for Cloudflare Turnstile.

    :param page: Playwright Page object which may or may not present a captcha
                 challenge needing to be solved.
    :param request: Scrapy request which caused this Playwright Page object to
                    be generated.
    :param spider: Scrapy spider which raised the request.
    """
    if await page.title() != "Just a moment..." or spider.captcha_type != "cloudflare_turnstile":
        # Page is not presenting or expected to present a Cloudflare Turnstile
        # captcha challenge.
        return

    # Wait for a few seconds for the Cloudflare iframe to be
    # requested/rendered. Whilst playwright_captcha will enter a polling loop
    # waiting for a Cloudflare iframe to appear, it will generate a noisy
    # exception in doing so. This noise can be avoided by waiting a few
    # seconds to start the captcha solver.
    await asyncio.sleep(3)

    solver = ClickSolver(framework=FrameworkType.CAMOUFOX, page=page)
    await solver.prepare()

    if getattr(spider, "captcha_selector_indicating_success"):
        # Preferred method for a spider to confirm that a click-solver captcha
        # has been successfully solved. The spider must set attribute
        # "captcha_selector_indicating_success" to a string which is an XPath
        # expression that will return one or more elements from the page only
        # if the captcha is successfully solved.
        #
        # For example, this XPath expression could detect the real website has
        # been successfully loaded by checking text of a h1 heading is the
        # website's name.
        #  captcha_selector_indicating_success = '//h1[text()="ACME Inc"]'
        await solver.solve_captcha(
            captcha_container=page,
            captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE,
            expected_content_selector=spider.captcha_selector_indicating_success,
        )
    else:
        # Fallback (default) mechanism where playwright_captcha tries to find
        # a signal from the page after clicking that the captcha is
        # successfully solved. For example, maybe there is a 1 second delay
        # where "Success" is printed, before the page redirects. This is
        # generally unreliable as a method for detecting successful solving
        # for a click-solver captcha.
        await solver.solve_captcha(captcha_container=page, captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE)


async def cloudflare_interstitial_solver(page: Page, request: Request, spider: Spider) -> None:
    """
    Click-solver for Cloudflare Interstitial.

    :param page: Playwright Page object which may or may not present a captcha
                 challenge needing to be solved.
    :param request: Scrapy request which caused this Playwright Page object to
                    be generated.
    :param spider: Scrapy spider which raised the request.
    """
    if await page.title() != "Just a moment..." or spider.captcha_type != "cloudflare_interstitial":
        # Page is not presenting or expected to present a Cloudflare
        # Interstitial captcha challenge.
        return

    # Wait for a few seconds for the Cloudflare challenge to load/render.
    await asyncio.sleep(5)

    solver = ClickSolver(framework=FrameworkType.CAMOUFOX, page=page)
    await solver.prepare()

    if getattr(spider, "captcha_selector_indicating_success"):
        # Preferred method for a spider to confirm that a click-solver captcha
        # has been successfully solved. The spider must set attribute
        # "captcha_selector_indicating_success" to a string which is an XPath
        # expression that will return one or more elements from the page only
        # if the captcha is successfully solved.
        #
        # For example, this XPath expression could detect the real website has
        # been successfully loaded by checking text of a h1 heading is the
        # website's name.
        #  captcha_selector_indicating_success = '//h1[text()="ACME Inc"]'
        await solver.solve_captcha(
            captcha_container=page,
            captcha_type=CaptchaType.CLOUDFLARE_INTERSTITIAL,
            expected_content_selector=spider.captcha_selector_indicating_success,
        )
    else:
        # Fallback (default) mechanism where playwright_captcha tries to find
        # a signal from the page after clicking that the captcha is
        # successfully solved. For example, maybe there is a 1 second delay
        # where "Success" is printed, before the page redirects. This is
        # generally unreliable as a method for detecting successful solving
        # for a click-solver captcha.
        await solver.solve_captcha(captcha_container=page, captcha_type=CaptchaType.CLOUDFLARE_INTERSTITIAL)
