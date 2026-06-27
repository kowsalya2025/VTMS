from .models import ContactQuery, Message, Trainer, Trainee, Intern, BusinessTeam

def unread_queries_count(request):
    """Context processor to make unread queries count available in all templates."""
    context = {
        'unread_queries_count': 0,
        'recent_queries': [],
        'unread_messages_count': 0,
        'recent_messages': [],
        'user_profile': None,
        'business_team_member': None,
        'trainer': None,
        'trainee': None,
        'intern': None
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        user = request.user
        
        # Admin gets contact queries and messages
        if user.role == 'ADMIN':
            context['unread_queries_count'] = ContactQuery.objects.filter(is_read=False).count()
            context['recent_queries'] = ContactQuery.objects.filter(is_read=False).order_by('-created_at')[:5]
        
        # Get user's profile
        if user.role == 'TRAINER':
            context['trainer'] = Trainer.objects.filter(user=user).first()
            context['user_profile'] = context['trainer']
        elif user.role == 'TRAINEE':
            context['trainee'] = Trainee.objects.filter(user=user).first()
            context['user_profile'] = context['trainee']
        elif user.role == 'INTERN':
            context['intern'] = Intern.objects.filter(user=user).first()
            context['user_profile'] = context['intern']
        elif user.role == 'BUSINESS_TEAM':
            context['business_team_member'] = BusinessTeam.objects.filter(user=user).first()
            context['user_profile'] = context['business_team_member']
        
        # All roles get messages
        unread_messages = Message.objects.filter(recipient=user, is_read=False)
        context['unread_messages_count'] = unread_messages.count()
        context['recent_messages'] = unread_messages.order_by('-created_at')[:5]
    
    return context