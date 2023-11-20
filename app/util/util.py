import uuid

allowlist = "qwertyuiopasdfghjklzxcvbnm1234567890 "

def sanitize_string(s: str):
    return "".join(list(filter(lambda c: c in allowlist, s.lower().strip()))).replace(" ", "-")

def generate_slug(*args):
    uid = ""
    if len(args) >= 2:
        uid = str(args[-1])
        args = args[:-1]
    res = '-'.join(list(map(sanitize_string, map(str, args))))
    if uid != "":
        res += "-" + uid
    return res

def get_uuid_from_slug(slug: str):
    try:
        return uuid.UUID("-".join(slug.split("-")[-5:]))
    except:
        return None

def is_uuid(s: str):
    return s and len(s.split("-")) == 5
