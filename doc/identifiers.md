Identifiers
===========

Generally speaking identifiers are used to uniquely label an object
even if it is renamed or has a duplicate object with the same properties,
i.e. identity tracking.
Or to find it quickly without looking at all its contents.

In other words, it's like a hash but persistent and with strong uniqueness
guarantees (a regular hash has equality checking as a fallback, which UUIDs
are designed not to need).

We need this primarily for masters (master.id), so we can associate layers to
their corresponding master and key the kerning by the masterId.

Master layers
-------------

|                    | Master layer          | Std layer |
|--------------------|-----------------------|-----------|
| masterId           | master.id             | master.id |
| masterLayer        | True                  | False     |
| name               | None (-> master.name) | "foo"     |

To this must add "glyph masters", an additional master added only at Layer
level. Instead of being anchored to a master, this layer will define its own
specific location (TODO add this in the data model).

Another mechanism is the GSUBing of glyph somewhere in the interpolation space
(otspec: Required Variation Alternates aka. rvrn), also TODO.
