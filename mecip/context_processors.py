from mecip.permissions import can_manage_records, can_manage_users


def user_permissions(request):
    user = request.user
    return {
        'can_manage_records': can_manage_records(user),
        'can_manage_users': can_manage_users(user),
    }
