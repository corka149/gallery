# Gallery

Just run `uv sync` and then rock!

## Cheatsheet

* `alembic revision -m "create image table"` creates a migration
* `alembic upgrade head` runs a migrations
* `msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base.po`
* `msgfmt -o locales/de/LC_MESSAGES/base.mo locales/de/LC_MESSAGES/base.po`

Create new user 
```python
import gallery.config as conf
import gallery.service as service
import gallery.db as db

c = conf.get_config()
db.init(c)

s = db.session()
u = db.User(username="sebastian", email="corka149@mailbox.org")
service.UserService(next(s)).save(u, "strong-password")
next(s)
```


## References

- [gettext language code](https://support.crowdin.com/developer/language-codes/)
