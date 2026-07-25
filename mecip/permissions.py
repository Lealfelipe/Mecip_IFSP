from django.contrib.auth.models import Group
from django.shortcuts import redirect, render


ROLE_EQUIPE = 'Equipe'
ROLE_COORDENADOR = 'Coordenador'
ROLE_SUPERADMIN = 'SuperAdmin'
USER_ROLE_NAMES = (ROLE_EQUIPE, ROLE_COORDENADOR, ROLE_SUPERADMIN)


def user_has_role(user, role_name):
    return user.is_authenticated and user.groups.filter(name=role_name).exists()


def is_team_user(user):
    return user_has_role(user, ROLE_EQUIPE)


def is_coordinator(user):
    return user_has_role(user, ROLE_COORDENADOR)


def is_superadmin(user):
    return user.is_authenticated and (user.is_superuser or user_has_role(user, ROLE_SUPERADMIN))


def can_manage_records(user):
    return user.is_authenticated and (is_coordinator(user) or is_superadmin(user))


def can_manage_users(user):
    return is_superadmin(user)


def can_view_all_records(user):
    return can_manage_records(user)


def user_belongs_to_report_team(user, report):
    return (
        user.is_authenticated
        and report.assigned_team is not None
        and report.assigned_team.users.filter(pk=user.pk).exists()
    )


def can_view_report_questionnaire(user, report):
    return can_manage_records(user) or user_belongs_to_report_team(user, report)


def can_answer_report(user, report):
    return can_manage_records(user) or user_belongs_to_report_team(user, report)


def assign_role(user, role_name):
    Group.objects.get_or_create(name=role_name)
    user.groups.remove(*Group.objects.filter(name__in=USER_ROLE_NAMES))
    user.groups.add(Group.objects.get(name=role_name))


def access_required(test_func):
    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('mecip:login')
            if not test_func(request.user):
                return render(
                    request,
                    'mecip/access_denied.html',
                    {'site_title': 'Acesso restrito'},
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
