from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import ForumPostForm
from .models import ForumPost


class RememberMeLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get("remember-me"):
            self.request.session.set_expiry(0)
        return response


@login_required
def home(request):
    if request.method == "POST":
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("home")
    else:
        form = ForumPostForm()

    return render(
        request,
        "home.html",
        {"form": form, "posts": ForumPost.objects.select_related("author").all()},
    )


@login_required
def calendar(request):
    return render(request, "calendar.html")
