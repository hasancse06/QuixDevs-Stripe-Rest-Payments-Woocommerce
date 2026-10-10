# Security policy

Do not post merchant keys, client secrets, order keys or customer data in public issues. Report security problems privately to the maintainer through a private contact method on https://hasan.online/; no dedicated security email has been verified for this project. Confirm the contact channel before sending sensitive evidence.

This build is development-only pending merchant acceptance. Supported inspection target: official Stripe extension 11.0.1. The addon never accepts raw card data and never marks an order paid. Do not clear locks or retry uncertain payments until the gateway/Stripe state has been reconciled.

See docs/security.md for authentication, cache, logging, rate-limit and recovery requirements. No production charge testing or live database changes are authorized by this repository.
