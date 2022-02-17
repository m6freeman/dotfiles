from concurrent.futures import Executor
from pathlib import Path, PurePath

from pynvim import Nvim
from pynvim_pp.api import get_cwd

from ..consts import SESSION_DIR
from ..fs.cartographer import new
from ..nvim.markers import markers
from ..settings.types import Settings
from ..view.render import render
from .ops import load_session
from .types import Selection, State, VCStatus


def initial(nvim: Nvim, pool: Executor, settings: Settings) -> State:
    cwd = PurePath(get_cwd(nvim))
    session_store = (
        Path(nvim.funcs.stdpath("cache")) / "chad_sessions"
        if settings.xdg
        else SESSION_DIR
    )

    session = (
        load_session(cwd, session_store=session_store) if settings.session else None
    )
    index = session.index if session and session.index is not None else {cwd}

    show_hidden = (
        session.show_hidden
        if session and session.show_hidden is not None
        else settings.show_hidden
    )
    enable_vc = (
        session.enable_vc
        if session and session.enable_vc is not None
        else settings.version_ctl.enable
    )

    selection: Selection = set()
    node = new(pool, root=cwd, index=index)
    mks = markers(nvim)
    vc = VCStatus()

    current = None
    filter_pattern = None

    derived = render(
        node,
        settings=settings,
        index=index,
        selection=selection,
        filter_pattern=filter_pattern,
        markers=mks,
        vc=vc,
        show_hidden=show_hidden,
        current=current,
    )

    state = State(
        pool=pool,
        session_store=session_store,
        index=index,
        selection=selection,
        filter_pattern=filter_pattern,
        show_hidden=show_hidden,
        follow=settings.follow,
        enable_vc=enable_vc,
        width=settings.width,
        root=node,
        qf=mks,
        vc=vc,
        current=current,
        derived=derived,
    )
    return state
