from django import forms
from .models import CustomUser
from apps.core.models import ShopSettings

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role', 'phone']

    def __init__(self, *args, **kwargs):
        allowed_roles = kwargs.pop('allowed_roles', None)
        super().__init__(*args, **kwargs)
        if allowed_roles is None:
            allowed_roles = ['manager', 'seller']
        self.fields['role'].choices = [
            choice for choice in self.fields['role'].choices
            if choice[0] in allowed_roles
        ]

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == 'admin':
            raise forms.ValidationError("La création d'un administrateur est interdite via ce formulaire.")
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = [
            'name',
            'logo',
            'phone',
            'email',
            'address',
            'currency',
            'ninea',
            'tax_number',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'ninea': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
