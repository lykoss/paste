from pygments.style import Style
from pygments.styles.default import DefaultStyle
from pygments.token import Error


class SimpleStyle(Style):
    styles = dict(DefaultStyle.styles.items())


SimpleStyle.styles[Error] = "border:"
