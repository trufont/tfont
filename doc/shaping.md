Text shaping
============

Steps
-----

1. Compile the feature code to a proper fea file.

2. Generate the feature tables (GDEF, GSUB, GPOS) and the font's glyphOrder
   (as layout engines use GIDs).

3. We need to build the `hb_font_t` from that.

4. Now we can shape, given an input (text or glyph names), and optionally
   {script, direction, language} (can be guessed from unicodings) and a list
   of features (by default, only recommended features such as `kern` and
   `liga`).

Detailed design
---------------

Features are the same for all masters/instances, therefore we can store the
engine as Font.engine, invalidation factors are then:

- Features themselves (Font.features, Font.featureClasses, Font.featureHeaders)
- Glyph added/deleted
- Glyph.name changed
- Glyph.unicode changed

Note: skip KernWriter and add kerning manually. How about MarkWriter?

font.engine has a factory (see caching.md) that takes the font, builds the
feature file (this could have a dedicated Font method--or all feature classes
could have a method that gives its text), compiles the tables
using `[glyph.name for glyph in font.glyphs]` as glyphOrder (should we add a
.notdef?), creates and store the LayoutEngine from the result that stores an
`hb_font_t`.

Then, each canvas holds a LayoutManager that maintains the caret and the
input text, and queries the LayoutEngine as needed.
