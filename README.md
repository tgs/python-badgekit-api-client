[![travis build](https://travis-ci.org/tgs/python-badgekit-api-client.svg)](https://travis-ci.org/tgs/python-badgekit-api-client/)
[![coverage](https://coveralls.io/repos/tgs/python-badgekit-api-client/badge.png)](https://coveralls.io/r/tgs/python-badgekit-api-client)

This is a partially-complete Python client for the BadgeKit API -
https://github.com/mozilla/badgekit-api

Using the functionality available so far, you can:
 * Connect to the BadgeKit API server, and check its health (`ping`),
 * Examine (`get`) badges, issuers, badge instances, and other objects,
 * List (`list`) the badges in an issuer, system, etc.
 * Create (`create`) objects:
    * Create issuer, system, and program objects.
    * Create badges.
    * Create badge instances, i.e. issue badges.

You cannot yet update or delete objects.  This will change soon.
