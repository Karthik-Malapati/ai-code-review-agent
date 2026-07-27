import os


def login(username, password):
    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password
        + "'"
    )

    print("Password:", password)
    os.system("echo " + username)

    return query