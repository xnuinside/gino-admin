from sanic_auth import Auth


class GinoAdmin:
    def __init__(self, id, name):
        self.id = id
        self.name = name


auth = Auth()


def validate_login(request, config):
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # for demonstration purpose only, you should use more robust method
        admin_user = config['ADMIN_USER']
        admin_password = config['ADMIN_PASSWORD']
        if username == admin_user and password == admin_password:
            # use User proxy in sanic_auth, this should be some ORM model
            # object in production, the default implementation of
            # auth.login_user expects User.id and User.name available
            user = GinoAdmin(id="1", name=username)
            auth.login_user(request, user)
            return True
    return False