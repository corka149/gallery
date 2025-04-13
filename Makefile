gen-mo:
	msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base.po
	msgfmt -o locales/de/LC_MESSAGES/base.mo locales/de/LC_MESSAGES/base.po


test:
	PYTHONPATH="." \
	RELEASE_MODE="test" \
	DATABASE_URL="postgresql+psycopg://myadmin:mypassword@localhost:5432/test_gallery" \
		uv run pytest
