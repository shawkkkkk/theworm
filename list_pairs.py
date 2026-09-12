"""
list_pairs.py

Reads the full paired-asset dropdown on the pons launchpad and prints every
option. Reuses the exact selectors already proven in rhlive.py's
set_pair_asset() -- this script only reads, it never picks one or launches
anything. No transaction is possible: the wallet is attached read-only
(allow_send=False), so even if something tried to sign, it couldn't.

Usage:
    python list_pairs.py
"""
import asyncio

from envcfg import load_env
from rhwallet import account, CHAIN_ID, RPC
from rhprovider import attach
from rhlive import (
    URL, accept_terms, dismiss_banners, go_dark,
    PAIR_TRIGGER_JS, MENU_JS,
)


async def main():
    from playwright.async_api import async_playwright

    env = load_env()
    acct = account(env)
    rpc = env.get("FLY_RH_RPC", RPC)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        async def refuse_send(tx):
            raise RuntimeError("read-only script: signing is disabled")

        await attach(page, acct, rpc, CHAIN_ID, allow_send=False,
                     on_send=refuse_send, log=print)

        print(f"loading {URL} ...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        await go_dark(page)
        await accept_terms(page)
        await dismiss_banners(page)
        await page.wait_for_timeout(1200)

        box = await page.evaluate(
            "(js) => { const e = eval(js); if (!e) return null;"
            " const r = e.getBoundingClientRect();"
            " return {x: r.x, y: r.y, w: r.width, h: r.height,"
            "         t: (e.textContent || '').trim()}; }", PAIR_TRIGGER_JS)
        if not box:
            print("could not find the paired-asset selector on the page")
            await browser.close()
            return
        print(f"current pair shown: {box['t']}")

        await page.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
        await page.wait_for_timeout(1400)

        names = await page.evaluate(
            """() => {
                 const m = document.querySelector('.launchpad-pair-menu');
                 if (!m) return null;
                 return [...m.querySelectorAll('button')]
                   .map(b => (b.textContent || '').trim())
                   .filter(Boolean);
               }""")

        if not names:
            print("pair menu did not open or has no options")
        else:
            print(f"\n{len(names)} pairable assets:\n")
            for n in names:
                print(f"  {n}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())