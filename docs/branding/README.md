# QuixDevs Stripe REST Payments branding

The presentation follows QuixDevs ProductClock’s navy and teal style: navy `#091827`, teal `#35e2cc`, white `#f4fbff` and muted blue `#b3c8d7`. Social and WordPress.org banners use the maintainer-supplied [QuixDevs logo](quixdevs-logo.png), with **Created by M A Hasan** at the bottom and the tagline above it.

The transparent logo is preserved byte-for-byte at its original 164 × 45 pixels. Its colors and proportions are unchanged. SVG compositions embed that exact PNG, so they work without a Desktop path or network request. The card, connector and verification tick are a separate original product mark, not a replacement company logo. No Stripe or WooCommerce logos or endorsement badges are used.

| Editable source | Export |
| --- | --- |
| [Supplied logo](quixdevs-logo.png) | Original QuixDevs wordmark |
| [Social preview](github-social-preview.svg) | [1280 × 640 PNG](github-social-preview.png) |
| [WordPress banner](wordpress-banner.svg) | [772 × 250](../../wordpress-org-assets/banner-772x250.png), [1544 × 500](../../wordpress-org-assets/banner-1544x500.png) |
| [Product mark](stripe-rest-payments-mark.svg) | [128 × 128](../../wordpress-org-assets/icon-128x128.png), [256 × 256](../../wordpress-org-assets/icon-256x256.png) |

PNGs are rendered and visually checked. To reproduce them with Node.js, Sharp and Arial installed, run `node tools/render-branding.mjs`. If Sharp is installed elsewhere, set `QUIXDEVS_SHARP_MODULE` to its absolute module path. This optional tooling adds no WordPress runtime dependency. SVGs can also be exported with a vector editor at the listed sizes.

The README embeds the social preview directly. GitHub’s separate link-sharing preview is set manually under **Repository Settings → Social Preview** using the same PNG. All promotional assets are excluded from the installable plugin ZIP.

The source uses the [MIT license](../../LICENSE). The supplied company logo remains maintainer branding; publisher rights review is recorded in [licensing](../licensing.md).
