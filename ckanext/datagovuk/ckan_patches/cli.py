from ckan.cli import user

from ckanext.datagovuk.lib.mailer import send_password_alert


def set_password(self):
    user.original_set_password(self)

    if len(self.args) > 1:
        import ckan.model as model

        username = self.args[1]
        user = model.User.get(username)
        send_password_alert(user)


user.original_set_password = user.set_password
user.set_password = set_password
