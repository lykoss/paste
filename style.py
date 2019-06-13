from pygments.styles.default import DefaultStyle
from pygments.token import Error


class SimpleStyle(DefaultStyle):
    def __init__(self):
        # don't put a red box around stuff
        del self.styles[Error]
