from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from itertools import chain, repeat
from typing import (
    Callable,
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Union,
)
from uuid import uuid4

from pynvim_pp.highlight import HLgroup
from std2.coloursys import rgb_to_hex

from ..consts import FM_HL_PREFIX
from .types import Mode


class _Style(IntEnum):
    bold = auto()
    dimmed = auto()
    italic = auto()
    underline = auto()
    blink = auto()
    blink_fast = auto()
    reverse = auto()
    hidden = auto()
    strikethrough = auto()


class _Ground(Enum):
    fore = auto()
    back = auto()


class _AnsiColour(IntEnum):
    black = auto()
    red = auto()
    green = auto()
    yellow = auto()
    blue = auto()
    magenta = auto()
    cyan = auto()
    white = auto()

    bright_black = auto()
    bright_red = auto()
    bright_green = auto()
    bright_yellow = auto()
    bright_blue = auto()
    bright_magenta = auto()
    bright_cyan = auto()
    bright_white = auto()


@dataclass(frozen=True)
class _Colour:
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class _Styling:
    styles: Set[_Style]
    foreground: Union[_AnsiColour, _Colour, None]
    background: Union[_AnsiColour, _Colour, None]


@dataclass(frozen=True)
class LSC:
    mode_pre: Mapping[Mode, HLgroup]
    mode_post: Mapping[Optional[Mode], HLgroup]
    exts: Mapping[str, HLgroup]
    name_glob: Mapping[str, HLgroup]


_ANSI_RANGE = range(256)
_RGB_RANGE = range(256)

_STYLE_TABLE: Mapping[str, _Style] = {str(code + 0): code for code in _Style}

_GROUND_TABLE: Mapping[str, _Ground] = {
    str(code): ground
    for code, ground in chain(
        zip(chain(range(30, 39), range(90, 98)), repeat(_Ground.fore)),
        zip(chain(range(40, 49), range(100, 108)), repeat(_Ground.back)),
    )
}

_COLOUR_TABLE: Mapping[str, _AnsiColour] = {
    str(code): colour
    for code, colour in chain(
        ((c + 29 if c <= 8 else c + 31, c) for c in _AnsiColour),
        ((c + 89 if c <= 8 else c + 91, c) for c in _AnsiColour),
    )
}

_RGB_TABLE: Set[str] = {"38", "48"}

_E_BASIC_TABLE: Mapping[int, _AnsiColour] = {i: c for i, c in enumerate(_AnsiColour)}

_E_GREY_TABLE: Mapping[int, _Colour] = {
    i: _Colour(r=s, g=s, b=s)
    for i, s in enumerate((round(step / 23 * 255) for step in range(24)), 232)
}


def _parse_8(codes: Iterator[str]) -> Union[_AnsiColour, _Colour, None]:
    try:
        ansi_code = int(next(codes, ""))
    except ValueError:
        return None
    else:
        if ansi_code in _ANSI_RANGE:
            basic = _E_BASIC_TABLE.get(ansi_code)
            if basic:
                return basic
            grey = _E_GREY_TABLE.get(ansi_code)
            if grey:
                return grey
            ratio = 255 / 5
            code = ansi_code - 16
            r = code // 36
            g = code % 36 // 6
            b = code % 36 % 6
            return _Colour(r=round(r * ratio), g=round(g * ratio), b=round(b * ratio))
        else:
            return None


def _parse_24(codes: Iterator[str]) -> Optional[_Colour]:
    try:
        r, g, b = int(next(codes, "")), int(next(codes, "")), int(next(codes, ""))
    except ValueError:
        return None
    else:
        if r in _RGB_RANGE and g in _RGB_RANGE and b in _RGB_RANGE:
            return _Colour(r=r, g=g, b=b)
        else:
            return None


_PARSE_TABLE: Mapping[
    str, Callable[[Iterator[str]], Union[_AnsiColour, _Colour, None]]
] = {
    "5": _parse_8,
    "2": _parse_24,
}


_SPECIAL_PRE_TABLE: Mapping[str, Mode] = {
    "bd": Mode.block_device,
    "cd": Mode.char_device,
    "do": Mode.door,
    "ex": Mode.executable,
    "ca": Mode.file_w_capacity,
    "di": Mode.folder,
    "ln": Mode.link,
    "mh": Mode.multi_hardlink,
    "or": Mode.orphan_link,
    "ow": Mode.other_writable,
    "pi": Mode.pipe,
    "so": Mode.socket,
    "st": Mode.sticky_dir,
    "tw": Mode.sticky_writable,
    "sg": Mode.set_gid,
    "su": Mode.set_uid,
}


_SPECIAL_POST_TABLE: Mapping[str, Optional[Mode]] = {
    "fi": Mode.file,
    "no": None,
}


_HL_STYLE_TABLE: Mapping[_Style, Optional[str]] = {
    _Style.bold: "bold",
    _Style.dimmed: None,
    _Style.italic: "italic",
    _Style.underline: "underline",
    _Style.blink: None,
    _Style.blink_fast: None,
    _Style.reverse: "reverse",
    _Style.hidden: None,
    _Style.strikethrough: "strikethrough",
}


def _parse_codes(
    codes: str,
) -> Iterator[Union[_Style, Tuple[_Ground, Union[_AnsiColour, _Colour]]]]:
    it = (code.lstrip("0") for code in codes.split(";"))
    for code in it:
        style = _STYLE_TABLE.get(code)
        if style:
            yield style
            continue
        ground = _GROUND_TABLE.get(code)
        ansi_colour = _COLOUR_TABLE.get(code)
        if ground and ansi_colour:
            yield ground, ansi_colour
        elif ground and code in _RGB_TABLE:
            code = next(it, "")
            parse = _PARSE_TABLE.get(code)
            if parse:
                colour = parse(it)
                if colour:
                    yield ground, colour


def _parse_styling(codes: str) -> _Styling:
    styles: Set[_Style] = set()
    colours: MutableMapping[_Ground, Union[_AnsiColour, _Colour]] = {}
    for ret in _parse_codes(codes):
        if isinstance(ret, _Style):
            styles.add(ret)
        elif isinstance(ret, tuple):
            ground, colour = ret
            colours[ground] = colour

    styling = _Styling(
        styles=styles,
        foreground=colours.get(_Ground.fore),
        background=colours.get(_Ground.back),
    )
    return styling


def _parseHLGroup(styling: _Styling, discrete_colours: Mapping[str, str]) -> HLgroup:
    fg, bg = styling.foreground, styling.background
    name = f"{FM_HL_PREFIX}_ls_{uuid4().hex}"
    cterm = {
        style
        for style in (_HL_STYLE_TABLE.get(style) for style in styling.styles)
        if style
    }
    ctermfg = fg.value - 1 if isinstance(fg, _AnsiColour) else None
    ctermbg = bg.value - 1 if isinstance(bg, _AnsiColour) else None
    guifg = (
        rgb_to_hex(fg.r, fg.g, fg.b)
        if isinstance(fg, _Colour)
        else (discrete_colours.get(fg.name) if isinstance(fg, _AnsiColour) else None)
    )
    guibg = (
        rgb_to_hex(bg.r, bg.g, bg.b)
        if isinstance(bg, _Colour)
        else (discrete_colours.get(bg.name) if isinstance(bg, _AnsiColour) else None)
    )
    group = HLgroup(
        name=name,
        cterm=cterm,
        ctermfg=ctermfg,
        ctermbg=ctermbg,
        guifg=guifg,
        guibg=guibg,
    )
    return group


def parse_lsc(ls_colours: str, discrete_colours: Mapping[str, str]) -> LSC:
    hl_lookup = {
        key: _parseHLGroup(_parse_styling(val), discrete_colours=discrete_colours)
        for key, _, val in (
            segment.partition("=") for segment in ls_colours.strip(":").split(":")
        )
    }

    mode_pre = {
        key: val
        for key, val in (
            (v, hl_lookup.pop(k, None)) for k, v in _SPECIAL_PRE_TABLE.items()
        )
        if val
    }

    mode_post = {
        key: val
        for key, val in (
            (v, hl_lookup.pop(k, None)) for k, v in _SPECIAL_POST_TABLE.items()
        )
        if val
    }

    _ext_keys = tuple(
        key for key in hl_lookup if key.startswith("*.") and key.count(".") == 1
    )
    exts = {key[1:]: hl_lookup.pop(key) for key in _ext_keys}

    lsc = LSC(exts=exts, mode_pre=mode_pre, mode_post=mode_post, name_glob=hl_lookup)
    return lsc
