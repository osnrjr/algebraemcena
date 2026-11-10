from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from apps.core.ratelimit import excedeu, ip_do_cliente


class LoginView(auth_views.LoginView):
    """Login local com rate limit de 5/min por IP (Doc ① §19; PROJECT_SPEC §10.1)."""

    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if excedeu('login', ip_do_cliente(request), settings.RATELIMIT_LOGIN):
            response = self.render_to_response(self.get_context_data(
                form=self.get_form(), bloqueado=True))
            response.status_code = 429
            response['Retry-After'] = '60'
            return response
        return super().post(request, *args, **kwargs)


class LogoutView(auth_views.LogoutView):
    http_method_names = ['post', 'options']


class PasswordResetView(auth_views.PasswordResetView):
    """Recuperação de senha com rate limit de 3/hora por IP (Doc ① §19)."""

    template_name = 'accounts/senha_pedir.html'
    email_template_name = 'accounts/senha_email.txt'
    subject_template_name = 'accounts/senha_assunto.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def post(self, request, *args, **kwargs):
        if excedeu('senha', ip_do_cliente(request), settings.RATELIMIT_SENHA):
            response = self.render_to_response(self.get_context_data(form=self.get_form(), bloqueado=True))
            response.status_code = 429
            response['Retry-After'] = '3600'
            return response
        return super().post(request, *args, **kwargs)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/senha_nova.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
