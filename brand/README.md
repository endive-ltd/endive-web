# Endive Limited — Logo Asset Pack

Vector versions of the Endive Limited logo, rebuilt from the original AI-generated artwork (`source/original-ai-logo.jpg`).

- **Icon:** rebuilt as clean bezier curves from the original. Its shape matches the original at a 98% pixel overlap. It is truly vector, so it stays sharp at any size.
- **Text:** set in **Montserrat** and converted to outlines, so no font needs to be installed to use the files. The font, weights, size and letter-spacing were matched to the original.

## Which file should I use?

| Need | File |
|---|---|
| Website header, documents, most uses | `svg/endive-logo-horizontal.svg` |
| Narrow / centred spaces (cover pages, signage) | `svg/endive-logo-stacked.svg` |
| On a green background or a photo | `svg/endive-logo-*-white.svg` |
| On a dark (black / charcoal) background | `svg/endive-logo-*-reversed.svg` (mint icon, white text) |
| Two-colour print, embroidery, vinyl (no gradient) | `*-flat.svg` |
| One-colour print, engraving, stamps | `*-black.svg` |
| Print shop / signage / merch | `pdf/` (vector PDF) or the `svg/` files |
| Word, PowerPoint, Google Docs, email | `png/…` (pick a size) |
| Favicon / app icon / social profile | `favicon/`, `svg/endive-app-icon-*.svg`, `social/profile-picture-800x800.png` |

## Folder contents

```
svg/        Master vector files (use these first)
  endive-logo-horizontal[-flat|-black|-white|-reversed].svg   icon + wordmark side by side (primary)
  endive-logo-stacked[-flat|-black|-white|-reversed].svg      icon above wordmark
  endive-wordmark[-flat|-black|-white|-reversed].svg          text only
  endive-icon[-black|-white].svg                    icon only, square artboard
  endive-app-icon-green.svg / -white.svg            rounded app tile
  endive-avatar-green-square.svg / -white-square    square tile (social avatars; platforms crop to a circle)
pdf/        Vector PDFs for printers (CMYK conversion is up to the printer, see colours below)
png/        Transparent PNGs. Logos 800/1600/3200/6400px wide; icons 256–2048px; tiles 180–1024px
favicon/    favicon.ico (16/32/48), favicon.svg, apple-touch-icon, android-chrome, site.webmanifest
social/     Open Graph image (light + dark), LinkedIn banner, X/Twitter header, email signature, profile picture
fonts/      Montserrat variable font + licence (SIL Open Font Licence, free for commercial use)
source/     The original AI artwork, for reference
```

## Colours

The palette was refined from the AI original so every green sits in one hue family (148–150°). The icon and the start of the "Endive" gradient are now the same colour, and the gradient ends in a deep green instead of near-black.

| Name | HEX | RGB | Approx. CMYK (coated) | Used for |
|---|---|---|---|---|
| Endive Green | `#26734A` | 38, 115, 74 | 80 25 80 15 | Icon, gradient start, brand colour, backgrounds |
| Deep Green | `#13442B` | 19, 68, 43 | 85 45 85 55 | Gradient end |
| Ink | `#101814` | 16, 24, 20 | 70 50 60 85 | "Limited", body text |
| Mint | `#7DCAA1` | 125, 202, 161 | 50 0 45 0 | Icon on dark backgrounds (`-reversed`) |
| White | `#FFFFFF` | 255, 255, 255 | — | Reversed versions |

CMYK depends on the printer and paper, so ask your printer to match the HEX value, or approve a proof. Endive Green on white has a 5.8:1 contrast ratio (passes WCAG AA for text).

## Typography

- **Endive:** Montserrat Bold (700). Spacing tightened optically: every letter gap is 72% of the font's own, with extra space between "i–v–e" so the diagonals don't touch.
- **Limited:** Montserrat Medium (500) at 1/√2 (70.7%) of the size of "Endive", letter gaps at 93% of the font's own.
- The left edges of "E" and "L" align exactly.
- Line gap ("Endive" baseline to "Limited" cap top) = 0.34 × the cap height of "Endive".
- Icon to text gap = 0.55 × cap height. The icon is centred vertically on the text block (cap top of "Endive" to baseline of "Limited").

Montserrat is free from Google Fonts: <https://fonts.google.com/specimen/Montserrat>. You only need it to typeset new text; the logo files already contain the text as shapes.

## Usage notes

- **Clear space:** keep empty space around the logo at least the height of the "E" in "Endive" on every side.
- **Minimum size:** horizontal logo 120 px / 30 mm wide; icon 24 px / 6 mm. The fine stripes in the icon blur together below about 32 px, which is expected for favicons.
- Don't stretch, recolour, rotate, add effects to, or re-type the logo. Use the supplied colour versions.

## Favicon HTML

Copy the files in `favicon/` to your site's root folder, then add this to `<head>`:

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#26734A">
```
