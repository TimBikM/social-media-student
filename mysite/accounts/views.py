from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            field.widget.attrs.update(
                {
                    "class": (
                        "block w-full rounded-lg border border-slate-300 bg-slate-50 "
                        "px-4 py-3 text-sm text-slate-900 placeholder-slate-400 "
                        "focus:border-blue-500 focus:bg-white focus:outline-none "
                        "focus:ring-2 focus:ring-blue-200"
                    ),
                    "autocomplete": (
                        "new-password" if name.startswith("password") else "username"
                    ),
                }
            )
        return form