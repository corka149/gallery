import gettext
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from gallery.service import AuthService as Auth

templates = Jinja2Templates(directory="templates")


class TemplateRenderer:
    def __init__(self, request: Request, auth: Annotated[Auth, Depends()]):
        self.auth = auth
        self.request = request
        lang = self.request.query_params.get("lang") or self.request.headers.get(
            "accept-language"
        )

        if "de" in lang:
            lang = "de"
        else:
            lang = "en"

        self.language_translations = gettext.translation(
            "base", "locales", languages=[lang]
        )

    def render(self, name: str, context: dict):
        context["_"] = self.translate
        context["is_authenticated"] = False
        context["year"] = datetime.now().year
        if self.request.cookies.get("gallery"):
            token = self.request.cookies.get("gallery")
            username = self.auth.verify_token(token)
            if username:
                context["is_authenticated"] = True

        return templates.TemplateResponse(
            request=self.request, name=name, context=context
        )

    def translate(self, message: str):
        return self.language_translations.gettext(message)
