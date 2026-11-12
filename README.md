# endive-web

Endive Limited's company page, a Worker on the Endive Cloudflare account (`52e65a2366c205fa0ea36ef06adf6262`). The email forwarder moved to the private `endive-ltd/endive-ops` repository on 2026-11-12.

| Folder | Worker | What |
|---|---|---|
| `site/` | `endive-website` | The company site on `endive.ie` and `www.endive.ie`: the home page (Tab and Soft Spot, the name story, contact hello@endive.ie), the brand guidelines at `/brand/`, and the s.151 company particulars in every footer |

## Brand

The logo, emblem, colours and type are documented at [endive.ie/brand](https://endive.ie/brand/), and every file lives in `site/public/brand/files/` (SVG, PNG, PDF, favicons, social images, Montserrat). `site/public/brand/Endive-Brand-Assets.zip` is the same files zipped; rebuild it if any of them change.

- Colours: Endive Green `#26734A`, Deep Green `#13442B`, Ink `#101814`, Mint `#7DCAA1`. Montserrat is the only typeface.
- Shared styles and scripts for every page: `site/public/assets/site.css` and `site.js`.
- The emblem on each page is inline SVG cut into four rings, so each ring can turn on its own. They spin into place once when the emblem comes on screen, and again only if someone clicks it. Reduced-motion settings turn the animation off.
- The site's favicons come from the brand pack and sit in `site/public/`.

## Deploy

- **Site:** automatic. Cloudflare Workers Builds is connected to this repo (27 Oct 2026): every push to `main` runs
  `npx wrangler deploy` in `site/` and updates `endive.ie` and `www.endive.ie`. Other branches only upload preview versions, and Preview URLs are off, so nothing but `main` reaches the domains.
- **Email forwarder:** by hand only, never on push, because it carries the founders' mail. From `email-forwarder/`:
  `npx wrangler login` as a member of the Endive account, then `npx wrangler deploy`. Send a test email to
  hello@endive.ie and admin@endive.ie straight after.

## Rules

- Only registered business names appear as brands or trading names on the site (Tab and Soft Spot; Foundry once its RBN1 is filed, decision 26 Oct 2026).
- The footer keeps the s.151 particulars: name, "private company limited by shares", registered in Ireland, number 828414, registered office.
- No secrets in this repo. The forwarder needs none; both destination Gmails must stay verified under Email Routing, Destination addresses.
- The forwarder source was recovered from the deployed Worker on 27 Oct 2026; Mark wrote it.
