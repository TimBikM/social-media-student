from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from myapp.models import Message


def _available_recipients(request):
    user_model = get_user_model()
    return user_model.objects.filter(is_active=True).exclude(pk=request.user.pk)


@login_required
def chat_page(request):
    return render(
        request,
        "chat.html",
        {
            "recipients": _available_recipients(request),
            "recipient": None,
            "conversation_messages": Message.objects.none(),
        },
    )


@login_required
def get_conversation(request, username):
    recipient = get_object_or_404(
        _available_recipients(request),
        username=username,
    )
    conversation_messages = Message.objects.filter(
        Q(sender=request.user, receiver=recipient)
        | Q(sender=recipient, receiver=request.user)
    ).select_related("sender", "receiver")

    return render(
        request,
        "chat.html",
        {
            "recipients": _available_recipients(request),
            "recipient": recipient,
            "conversation_messages": conversation_messages,
        },
    )


@login_required
@require_POST
def send_message(request, username):
    recipient = get_object_or_404(
        _available_recipients(request),
        username=username,
    )
    content = request.POST.get("content", "").strip()

    if not content:
        messages.error(request, "Write a message before sending.")
    elif len(content) > 2000:
        messages.error(request, "Messages must be 2,000 characters or fewer.")
    else:
        Message.objects.create(
            sender=request.user,
            receiver=recipient,
            content=content,
        )

    return redirect("chat_conversation", username=recipient.username)
