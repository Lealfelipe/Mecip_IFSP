from django.shortcuts import render, redirect
from mecip.forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from mecip.forms import CustomAuthenticationForm

def register(request):
    form = RegisterForm()


    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário registrado')
            return redirect('mecip:login')

    return render(
        request,
        'mecip/register.html',
        {
            'form': form
        }
    )


def login_view(request):
    form = CustomAuthenticationForm(request)

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data= request.POST)

        if form.is_valid():
            user = form.get_user()
            messages.success(request, 'Logado com sucesso!')
            auth.login(request, user)
            print(user)
            return redirect('mecip:index')
        messages.error(request, 'Login inválido')

    return render(
        request,
        'mecip/login.html',
        {
            'form': form
        }
    )

@login_required(login_url='mecip:login')
def logout_view(request):
    auth.logout(request)
    return redirect('mecip:login')