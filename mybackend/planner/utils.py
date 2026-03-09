def fix_homedepot_url(url):
    """
    If the url is a Home Depot API url (apionline.homedepot.com),
    convert it to a user-facing homedepot.com url.
    """
    if url and 'apionline.homedepot.com/p/' in url:
        return url.replace('apionline.homedepot.com', 'homedepot.com')
    return url


# API Call Throttling Utilities

class APICallLimitExceeded(Exception):
    """Exception raised when user exceeds API call limit for a service."""
    def __init__(self, service, limit, current_count):
        self.service = service
        self.limit = limit
        self.current_count = current_count
        super().__init__(
            f"Daily limit of {limit} {service} calls exceeded. "
            f"You have made {current_count} calls today. Please try again tomorrow."
        )


def check_api_call_limit(user, service):
    """
    Check if user has exceeded their daily API call limit.
    
    Args:
        user: Django User object
        service: 'serpapi' or 'openai'
    
    Raises:
        APICallLimitExceeded: If user has exceeded limit
    
    Returns:
        tuple: (current_count, limit) if under limit
    """
    from django.conf import settings
    from planner.models import APICallLog
    
    # Get limit from settings
    if service == 'serpapi':
        limit = settings.API_CALLS_PER_DAY_SERPAPI
    elif service == 'openai':
        limit = settings.API_CALLS_PER_DAY_OPENAI
    else:
        raise ValueError(f"Unknown service: {service}")
    
    # Get current count
    current_count = APICallLog.get_call_count(user, service)
    
    # Check if limit exceeded
    if current_count >= limit:
        raise APICallLimitExceeded(service, limit, current_count)
    
    return (current_count, limit)


def increment_api_call(user, service):
    """
    Increment API call count for user and service.
    
    Args:
        user: Django User object
        service: 'serpapi' or 'openai'
    
    Returns:
        APICallLog object with updated count
    """
    from planner.models import APICallLog
    
    return APICallLog.increment_call_count(user, service)


def get_api_call_status(user, service):
    """
    Get current API call status for user.
    
    Args:
        user: Django User object
        service: 'serpapi' or 'openai'
    
    Returns:
        dict: {'service': str, 'limit': int, 'used': int, 'remaining': int, 'reset_time': str}
    """
    from django.conf import settings
    from django.utils import timezone
    from planner.models import APICallLog
    
    # Get limit from settings
    if service == 'serpapi':
        limit = settings.API_CALLS_PER_DAY_SERPAPI
    elif service == 'openai':
        limit = settings.API_CALLS_PER_DAY_OPENAI
    else:
        raise ValueError(f"Unknown service: {service}")
    
    # Get current count
    used = APICallLog.get_call_count(user, service)
    remaining = max(0, limit - used)
    
    # Calculate reset time (midnight UTC)
    now = timezone.now()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    reset_time = tomorrow.isoformat()
    
    return {
        'service': service,
        'limit': limit,
        'used': used,
        'remaining': remaining,
        'reset_time': reset_time,
        'limit_exceeded': used >= limit,
    }
