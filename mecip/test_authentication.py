from django.contrib.auth.models import User
from django.test import TestCase


class LoginRequiredMiddlewareTests(TestCase):
    def test_dashboard_redireciona_usuario_nao_autenticado(self):
        response = self.client.get('/')

        self.assertRedirects(response, '/login/?next=/')

    def test_outra_pagina_redireciona_usuario_nao_autenticado(self):
        response = self.client.get('/curso/')

        self.assertRedirects(response, '/login/?next=/curso/')

    def test_pagina_de_login_continua_publica(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)

    def test_usuario_autenticado_acessa_dashboard(self):
        user = User.objects.create_user(
            username='usuario',
            password='senha-segura',
        )
        self.client.force_login(user)

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

    def test_api_continua_retornando_erro_de_autenticacao(self):
        response = self.client.get('/api/v1/campus/')

        self.assertEqual(response.status_code, 401)


class UserCreationPermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='senha-segura',
        )
        self.regular_user = User.objects.create_user(
            username='usuario-comum',
            password='senha-segura',
        )

    def test_admin_acessa_formulario_de_criacao(self):
        self.client.force_login(self.admin)

        response = self.client.get('/user/register/')

        self.assertEqual(response.status_code, 200)

    def test_usuario_comum_recebe_acesso_negado(self):
        self.client.force_login(self.regular_user)

        response = self.client.get('/user/register/')

        self.assertEqual(response.status_code, 403)

    def test_usuario_comum_nao_pode_criar_usuario_via_post(self):
        self.client.force_login(self.regular_user)

        response = self.client.post('/user/register/', {
            'first_name': 'Novo',
            'last_name': 'Usuario',
            'email': 'novo@example.com',
            'username': 'novo-usuario',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='novo-usuario').exists())

    def test_link_de_criacao_aparece_no_menu_do_admin(self):
        self.client.force_login(self.admin)

        response = self.client.get('/')

        self.assertContains(response, '/user/register/')

    def test_link_de_criacao_nao_aparece_para_usuario_comum(self):
        self.client.force_login(self.regular_user)

        response = self.client.get('/')

        self.assertNotContains(response, '/user/register/')

    def test_admin_cria_usuario_e_retorna_formulario_vazio(self):
        self.client.force_login(self.admin)

        response = self.client.post('/user/register/', {
            'first_name': 'Novo',
            'last_name': 'Usuario',
            'email': 'novo@example.com',
            'username': 'novo-usuario',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        }, follow=True)

        self.assertRedirects(response, '/user/register/')
        self.assertContains(
            response,
            'Usuário novo-usuario criado com sucesso.',
        )
        self.assertFalse(response.context['form'].is_bound)
        self.assertTrue(
            User.objects.filter(username='novo-usuario').exists()
        )

    def test_pagina_de_criacao_nao_exibe_link_entrar(self):
        self.client.force_login(self.admin)

        response = self.client.get('/user/register/')

        self.assertNotContains(response, '>Entrar</a>')

    def test_pagina_de_login_nao_exibe_link_cadastre_se(self):
        response = self.client.get('/login/')

        self.assertNotContains(response, 'Cadastre-se')
