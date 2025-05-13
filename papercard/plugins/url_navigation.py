from js import document, console, window


class UrlNavigationPlugin:
    def __init__(self, app):
        self.app = None

        self._loc = loc = document.location
        self.base = loc.origin + loc.pathname + "#%s"

    def get_cardname_from_url(self):
        return document.location.hash.replace("#", "")

    def after_show_card(self, app, card):
        console.log("-------> after_show_card", card.name)
        document.location.href = self.base % card.name
        window.hljs.highlightAll();

