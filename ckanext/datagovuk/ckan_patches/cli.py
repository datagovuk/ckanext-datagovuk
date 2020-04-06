import ckan.lib.cli

from ckanext.datagovuk.lib.mailer import send_password_alert


def set_password(self):
    ckan.cli.user.original_set_password(self)

    if len(self.args) > 1:
        import ckan.model as model

        username = self.args[1]
        user = model.User.get(username)
        send_password_alert(user)


ckan.cli.user.original_set_password = ckan.cli.user.set_password
ckan.cli.user.set_password = set_password
