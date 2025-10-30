import re
from datetime import datetime
from django.utils.timezone import make_aware
import pytz

LOG_PATTERN = re.compile(
    r'(?P<remote_addr>\S+) '                     # IP
    r'(?P<remote_logname>\S+) '                  # identd
    r'(?P<remote_user>\S+) '                     # user
    r'\[(?P<time>.*?)\] '                        # [10/Oct/2000:13:55:36 -0700]
    r'"(?P<request>.*?)" '                       # "GET /index.html HTTP/1.0"
    r'(?P<status>\d{3}) '                        # 200
    r'(?P<body_bytes_sent>\S+)'                  # 2326 or '-'
    r'(?: "(?P<referer>.*?)" "(?P<user_agent>.*?)")?'  # optional referer and user-agent
)

TIME_FORMAT = '%d/%b/%Y:%H:%M:%S %z'

def parse_log_line(line, default_tz='UTC'):
    m = LOG_PATTERN.match(line)
    if not m:
        return None

    gd = m.groupdict()
    # parse time
    try:
        dt = datetime.strptime(gd['time'], TIME_FORMAT)
        # make timezone-aware (datetime already has tzinfo from %z)
    except Exception:
        # fallback: naive parse and set UTC
        try:
            dt = datetime.strptime(gd['time'].split()[0], '%d/%b/%Y:%H:%M:%S')
            import pytz
            tz = pytz.timezone(default_tz)
            dt = make_aware(dt, timezone=tz)
        except Exception:
            return None

    request = gd.get('request') or ''
    method = path = proto = ''
    if request and request != '-':
        parts = request.split()
        if len(parts) >= 1:
            method = parts[0]
        if len(parts) >= 2:
            path = parts[1]
        if len(parts) >= 3:
            proto = parts[2]

    body_bytes = gd.get('body_bytes_sent')
    try:
        body_bytes = int(body_bytes) if body_bytes and body_bytes != '-' else 0
    except:
        body_bytes = 0

    return {
        'remote_addr': gd.get('remote_addr'),
        'remote_user': None if gd.get('remote_user') == '-' else gd.get('remote_user'),
        'timestamp': dt,
        'request_method': method,
        'request_path': path,
        'protocol': proto,
        'status': int(gd.get('status') or 0),
        'body_bytes_sent': body_bytes,
        'referer': None if gd.get('referer') == '-' else gd.get('referer'),
        'user_agent': None if gd.get('user_agent') == '-' else gd.get('user_agent'),
        'raw_line': line.strip(),
    }