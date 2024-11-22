from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile

# Mensagens centralizadas para validações
EMAIL_IN_USE_MSG = "Este email já está em uso."
PASSWORD_MISMATCH_MSG = "As senhas não coincidem."
INVALID_PHONE_MSG = (
    "O número de telefone deve estar no formato (99) 99999-9999 ou (99) 9999-9999."
)


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu email",
            }
        ),
        label="Email",
    )

    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite seu número de telefone",
            }
        ),
        label="Número de Telefone",
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite sua senha",
            }
        ),
        label="Senha",
        validators=[validate_password],  # Validação diretamente no campo
        help_text="A senha deve conter pelo menos 8 caracteres, incluindo números, letras maiúsculas e minúsculas, e caracteres especiais.",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirme sua senha",
            }
        ),
        label="Confirme a Senha",
    )

    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]
        labels = {
            "username": "Usuário",
        }

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Digite seu usuário",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError(EMAIL_IN_USE_MSG)
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise ValidationError(PASSWORD_MISMATCH_MSG, code="password_mismatch")
        return confirm_password

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        phone_regex = re.compile(r"^\(?\d{2}\)?\s?\d{4,5}-\d{4}$")
        if not phone_regex.match(phone_number):
            raise ValidationError(INVALID_PHONE_MSG)
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            # Cria o perfil do usuário associado
            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(
                    user=user, phone_number=self.cleaned_data["phone_number"]
                )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nome de usuário",
            }
        ),
    )

    password = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Senha",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Credenciais inválidas.")
            if user and not user.is_active:
                raise forms.ValidationError("Este usuário está inativo.")
        return cleaned_data

class EditUserForm(forms.Form):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'descricao']
        labels = {
            'username': 'Usuário',
            'password': 'Senha',
        }
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise ValidationError('O nome de usuário deve ter pelo menos 4 caracteres.')
        if username.isdigit():
            raise ValidationError('O nome de usuário não pode conter apenas números.')
        if re.search(r'[\W_]', username):
            raise ValidationError('O nome de usuário não deve conter caracteres especiais.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso.')
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        phone_regex = re.compile(r'^\(\d{2}\)\s?\d{4,5}-\d{4}$')
        if not phone_regex.match(phone_number):
            raise ValidationError('O número de telefone deve estar no formato (99) 99999-9999 ou (99) 9999-9999.')
        return phone_number