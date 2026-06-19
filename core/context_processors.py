from .models import ContactQuery, Message

def unread_queries_count(request):
    """Context processor to make unread queries count available in all templates."""
    context = {
        'unread_queries_count': 0,
        'recent_queries': [],
        'unread_messages_count': 0,
        'recent_messages': []
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        user = request.user
        
        # Admin gets contact queries and messages
        if user.role == 'ADMIN':
            context['unread_queries_count'] = ContactQuery.objects.filter(is_read=False).count()
            context['recent_queries'] = ContactQuery.objects.filter(is_read=False).order_by('-created_at')[:5]
        
        # All roles get messages
        unread_messages = Message.objects.filter(recipient=user, is_read=False)
        context['unread_messages_count'] = unread_messages.count()
        context['recent_messages'] = unread_messages.order_by('-created_at')[:5]
    
    return context