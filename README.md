# endive-web

Endive Limited's company page and email forwarder, both Workers on the Endive Cloudflare account (`52e65a2366c205fa0ea36ef06adf6262`). Private repo; moves to the company GitHub organisation when it exists.

| Folder | Worker | What |
|---|---|---|
| `site/` | `endive-website` | The company site on `endive.ie` and `www.endive.ie`: the home page (Tab and Soft Spot, the name story, contact hello@endive.ie) and the s.151 company particulars in every footer |
| `email-forwarder/` | `endive-hello-forward` | Copies mail for hello@endive.ie, admin@endive.ie and hello@softspotgifts.com to both founders' Gmails |

## Brand

The brand pack is internal and lives in `brand/` (SVG, PNG, PDF, favicons, social images, Montserrat, and a README with the rules); it is not published on the site. Old `/brand` links redirect to the home page (`site/public/_redirects`).

- Colours: Endive Green `#26734A`, Deep Green `#13442B`, Ink `#101814`, Mint `#7DCAA1`. Montserrat is the only typeface.
- Shared styles and scripts for every page: `site/public/assets/site.css` and `site.js`. The header and footer logos are `assets/logo.svg` and `assets/logo-reversed.svg`.
- The emblem spin is `assets/emblem-spin.js`. Each of the four rings is drawn as the tread of a wheel seen at an angle (its two pinched ends are where the tread turns away). On arrival the rings, one after another, roll once on their axles like tyres: each outline stays put while its grooves travel along the ring, following their own curves, and pass under the next ring at its edge, lit in 3D. The emblem ends exactly on the logo. It draws with WebGL from `emblem-rings.png` (each ring's tread: angle round the wheel by position across it; the logo's grooves on the front, newly drawn grooves in the same style round the hidden part), `emblem-edges.png` (each ring's two edges, so grooves keep their place across the ring), `emblem-windows.png` and `emblem-tint.png` (which part of the emblem is which ring; borders run along the front ring's strands), `emblem-shade.png` (the soft shadow where a ring passes under its neighbour), `emblem-rim.png` (the outline that stays solid) and `emblem-spin.json`. Clicking the emblem replays it. No WebGL or reduced motion: the emblem stays still.
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
