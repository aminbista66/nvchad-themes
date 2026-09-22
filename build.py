"""Generate Zed themes from NvChad base46 palettes.

Usage: python3 build.py   (writes themes/nvchad-<name>.json)
Add a theme: append its base46 file name to THEMES and rerun.
"""

import json
import re
import urllib.request

# Version is subject to change, please check the base46 repo for the latest version
BASE46 = "https://raw.githubusercontent.com/NvChad/base46/v3.0/lua/base46/themes/{}.lua"
THEMES = ["ashes", "aquarium", "chadtain", "chocolate", "kanagawa-dragon", "monochrome", "mountain", "nightlamp"]

# base46 polish_hl groups -> Zed syntax keys. Groups Zed has no key for are skipped.
POLISH = {
    "Operator": ["operator"],
    "Statement": ["keyword"],
    "PreProc": ["preproc"],
    "@operator": ["operator"],
    "@variable": ["variable"],
    "@variable.member": ["variable.member", "property"],
    "@variable.parameter": ["variable.parameter"],
    "@attribute": ["attribute"],
    "@constant": ["constant"],
    "@function.builtin": ["function.builtin"],
    "@punctuation.bracket": ["punctuation.bracket"],
}

T = "#00000000"


def fetch(name):
    lua = urllib.request.urlopen(BASE46.format(name)).read().decode()
    palette = dict(re.findall(r'(\w+)\s*=\s*"(#[0-9a-fA-F]{6})"', lua))
    # base_16 entries may reference base_30 colors, e.g. base0A = M.base_30.cyan
    for key, ref in re.findall(r'(\w+)\s*=\s*M\.base_30\.(\w+)\s*,', lua):
        palette[key] = palette[ref]
    polish = re.findall(r'\[?"?([@\w.]+)"?\]?\s*=\s*\{\s*fg\s*=\s*M\.base_(?:30|16)\.(\w+)', lua)
    result = re.search(r'M\.type\s*=\s*"(\w+)"', lua)
    if not result:
        raise ValueError(f"Could not find M.type in {name}")

    kind = result.group(1)
    return palette, polish, kind


def theme(name, c, polish, kind):
    def state(color, bg=None, border=None):
        return color, bg or c[color] + "22", border or c[color]

    status = {
        "conflict": state("orange"), "created": state("green"), "deleted": state("red"),
        "modified": state("blue"), "error": state("red"), "warning": state("yellow"),
        "info": state("blue"), "hint": state("purple"), "success": state("green"),
        "renamed": state("teal"),
        **{k: state("light_grey", c["black"], c["line"]) for k in ("hidden", "ignored", "unreachable", "predictive")},
    }
    style = {
        "background": c["darker_black"],
        "surface.background": c["darker_black"],
        "elevated_surface.background": c["black2"],
        "panel.background": c["darker_black"],
        "panel.focused_border": c["line"],
        "pane.focused_border": c["line"],
        "border": c["line"],
        "border.variant": c["line"],
        "border.focused": c["blue"],
        "border.selected": c["blue"],
        "border.transparent": T,
        "border.disabled": c["one_bg"],
        "element.background": c["one_bg"],
        "element.hover": c["one_bg2"],
        "element.active": c["one_bg3"],
        "element.selected": c["one_bg2"],
        "element.disabled": c["one_bg"],
        "ghost_element.background": T,
        "ghost_element.hover": c["one_bg"],
        "ghost_element.active": c["one_bg2"],
        "ghost_element.selected": c["one_bg2"],
        "ghost_element.disabled": T,
        "drop_target.background": c["blue"] + "22",
        "text": c["white"],
        "text.muted": c["base04"],
        "text.placeholder": c["light_grey"],
        "text.disabled": c["grey_fg"],
        "text.accent": c["blue"],
        "icon": c["white"],
        "icon.muted": c["light_grey"],
        "icon.disabled": c["grey"],
        "icon.placeholder": c["light_grey"],
        "icon.accent": c["nord_blue"],
        "status_bar.background": c["statusline_bg"],
        "title_bar.background": c["darker_black"],
        "title_bar.inactive_background": c["darker_black"],
        "toolbar.background": c["black"],
        "tab_bar.background": c["darker_black"],
        "tab.inactive_background": c["darker_black"],
        "tab.active_background": c["black"],
        "search.match_background": c["blue"] + "44",
        "scrollbar.thumb.background": c["grey"] + "88",
        "scrollbar.thumb.hover_background": c["light_grey"],
        "scrollbar.thumb.border": T,
        "scrollbar.track.background": T,
        "scrollbar.track.border": T,
        "editor.foreground": c["white"],
        "editor.background": c["black"],
        "editor.gutter.background": c["black"],
        "editor.subheader.background": c["black2"],
        "editor.active_line.background": c["black2"],
        "editor.highlighted_line.background": c["black2"],
        "editor.line_number": c["grey"],
        "editor.active_line_number": c["white"],
        "editor.invisible": c["one_bg3"],
        "editor.wrap_guide": c["line"],
        "editor.active_wrap_guide": c["one_bg3"],
        "editor.indent_guide": c["line"],
        "editor.indent_guide_active": c["grey"],
        "editor.document_highlight.read_background": c["one_bg2"],
        "editor.document_highlight.write_background": c["one_bg3"],
        "terminal.background": c["black"],
        "terminal.foreground": c["white"],
        "terminal.bright_foreground": c["base07"],
        "terminal.dim_foreground": c["base04"],
        "link_text.hover": c["cyan"],
    }
    # ansi name -> (normal, bright, dim)
    ansi = {
        "black": ("black", "grey", "darker_black"),
        "red": ("red", "red", "red"),
        "green": ("green", "vibrant_green", "green"),
        "yellow": ("yellow", "sun", "yellow"),
        "blue": ("blue", "nord_blue", "blue"),
        "magenta": ("purple", "pink", "dark_purple"),
        "cyan": ("cyan", "teal", "cyan"),
        "white": ("white", "base07", "base04"),
    }
    for a, (n, b, d) in ansi.items():
        style[f"terminal.ansi.{a}"] = c[n]
        style[f"terminal.ansi.bright_{a}"] = c[b]
        style[f"terminal.ansi.dim_{a}"] = c[d]
    for k, (color, bg, border) in status.items():
        style[k], style[k + ".background"], style[k + ".border"] = c[color], bg, border
    style["players"] = [
        {"cursor": c[p], "background": c[p], "selection": c[p] + "33"}
        for p in ("blue", "green", "pink", "orange", "purple", "teal", "red", "yellow")
    ]

    # Zed syntax key -> base46 palette key (mirrors base46's treesitter mapping)
    syntax = {
        "attribute": "base0A", "boolean": "base09", "comment": "grey_fg", "comment.doc": "grey_fg",
        "constant": "base08", "constructor": "base0C", "embedded": "base05", "emphasis": "base0D",
        "emphasis.strong": "base09", "enum": "base0A", "function": "base0D", "function.builtin": "base0D",
        "function.method": "base0D", "hint": "light_grey", "keyword": "base0E", "label": "base0A",
        "link_text": "base0C", "link_uri": "base0B", "number": "base09", "operator": "base05",
        "predictive": "light_grey", "preproc": "base0A", "primary": "base05", "property": "base08",
        "punctuation": "base0F", "punctuation.bracket": "base0F", "punctuation.delimiter": "base0F",
        "punctuation.list_marker": "base08", "punctuation.special": "base0F", "string": "base0B",
        "string.escape": "base0C", "string.regex": "base0C", "string.special": "base0C",
        "string.special.symbol": "base08", "tag": "base08", "text.literal": "base0B", "title": "base0D",
        "type": "base0A", "type.builtin": "base0A", "variable": "base05", "variable.member": "base08",
        "variable.parameter": "base08", "variable.special": "base09", "variant": "base0A",
    }
    for group, key in polish:
        for zed_key in POLISH.get(group, []):
            syntax[zed_key] = key
    fonts = {
        "comment": {"font_style": "italic"}, "comment.doc": {"font_style": "italic"},
        "emphasis": {"font_style": "italic"}, "emphasis.strong": {"font_weight": 700},
        "link_uri": {"font_style": "italic"}, "predictive": {"font_style": "italic"},
        "title": {"font_weight": 700},
    }
    style["syntax"] = {k: {"color": c[v], **fonts.get(k, {})} for k, v in syntax.items()}

    title = "NvChad " + name.replace("-", " ").title()
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": title,
        "author": "NvChad (base46), ported for Zed",
        "themes": [{"name": title, "appearance": kind, "style": style}],
    }


if __name__ == "__main__":
    for name in THEMES:
        palette, polish, kind = fetch(name)
        with open(f"themes/nvchad-{name}.json", "w") as f:
            json.dump(theme(name, palette, polish, kind), f, indent=2)
            f.write("\n")
        print("wrote", name)
