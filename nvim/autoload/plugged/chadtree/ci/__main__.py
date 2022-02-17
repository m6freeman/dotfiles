from json import dump

from std2.graphlib import recur_sort
from std2.pickle.encoder import new_encoder

from chad_types import ARTIFACT, Artifact

from .icon_colours import load_icon_colours
from .ls_colours import load_ls_colours
from .text_decorations import load_text_decors


def main() -> None:
    encode = new_encoder[Artifact](Artifact)
    ls_colours = load_ls_colours()
    icon_colours = load_icon_colours()
    icons, text_colours = load_text_decors()

    artifact = Artifact(
        icons=icons,
        ls_colours=ls_colours,
        icon_colours=icon_colours,
        text_colours=text_colours,
    )

    json = recur_sort(encode(artifact))
    with ARTIFACT.open("w") as fd:
        dump(json, fd, ensure_ascii=False, check_circular=False, indent=2)


main()
