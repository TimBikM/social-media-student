from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render


class RememberMeLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get("remember-me"):
            self.request.session.set_expiry(0)
        return response


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def calendar(request):
    return render(request, "calendar.html")
