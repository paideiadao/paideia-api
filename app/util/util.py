
allowlist = "qwertyuiopasdfghjklzxcvbnm1234567890 "

def sanitize_string(s: str):
    return "".join(list(filter(lambda c: c in allowlist, s.lower().strip()))).replace(" ", "-")

def generate_slug(*args):
    return '-'.join(list(map(sanitize_string, map(str, args))))
