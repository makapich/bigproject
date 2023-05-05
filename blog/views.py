from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import ContactUsForm
from .models import BlogPost, BlogUser, Comment
from .tasks import send_mail as celery_send_mail

User = get_user_model()


class RegisterFormView(SuccessMessageMixin, generic.FormView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy("home")
    success_message = 'Successfully registered, welcome!'

    def form_valid(self, form):
        user = form.save()
        user = authenticate(username=user.username, password=form.cleaned_data.get("password1"))
        login(self.request, user)
        blog_user = BlogUser(user=user)
        blog_user.save()
        return super(RegisterFormView, self).form_valid(form)


class UpdateProfile(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = BlogUser
    fields = ["email", "bio", "avatar", "website"]
    template_name = 'registration/update_profile.html'
    success_url = reverse_lazy("home")
    success_message = 'The profile was updated successfully!'

    def get_object(self, queryset=None):
        user = self.request.user
        return user.bloguser

    def form_valid(self, form):

        avatar = form.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 1000000:
                form.add_error('avatar', 'Avatar file size cannot exceed 1 Mb.')
                return self.form_invalid(form)

        if form.cleaned_data.get('email'):
            form.instance.user.email = form.cleaned_data.get('email')
            form.instance.user.save()

        return super().form_valid(form)


class UserProfile(generic.DetailView):
    model = BlogUser
    template_name = "registration/profile.html"
    slug_field = 'user__username'
    slug_url_kwarg = 'username'
    paginate_by = 12

    def get_object(self, queryset=None):
        username = self.kwargs.get(self.slug_url_kwarg)
        user = get_object_or_404(BlogUser, user__username=username)
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        posts = BlogPost.objects.select_related('author__bloguser').filter(is_published=True, author=user.user).\
            order_by('-created_at')
        drafts = BlogPost.objects.select_related('author__bloguser').filter(is_published=False, author=user.user).\
            order_by('-created_at')
        context['posts'] = posts
        context['drafts'] = drafts
        return context


class BlogPostListView(generic.ListView):
    model = BlogPost
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author__bloguser').filter(is_published=True).order_by('-created_at')
        return queryset


class BlogPostCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = BlogPost
    template_name = 'blog/blogpost_create.html'
    fields = ['title', 'text', 'image']
    success_url = reverse_lazy('home')
    success_message = 'The publication was created!'

    def form_valid(self, form):
        form.instance.author = self.request.user

        image = form.cleaned_data.get('image')
        if image:
            if image.size > 3000000:
                form.add_error('image', 'Image file size cannot exceed 3 Mbs.')
                return self.form_invalid(form)

        text = form.cleaned_data.get('text')
        if text:
            form.instance.short_description = text[:50] + '...' if len(text) > 50 else text

        if 'publish' in self.request.POST:
            form.instance.is_published = True

            scheme = self.request.scheme
            current_site = get_current_site(self.request)
            url = reverse("profile", args=[form.instance.author.username])
            absolute_url_user = f'{scheme}://{current_site.domain}{url}'

            # Email to admin
            subject = 'New post notification!'
            message = ''
            html_message = f'New post by <a href="{absolute_url_user}">{form.instance.author}</a><br>Check it out!'
            from_email = settings.NOREPLY_EMAIL
            to_email = [user.email for user in User.objects.filter(is_staff=True)]
            celery_send_mail.apply_async((subject, message, from_email, to_email, html_message))

        return super().form_valid(form)


class BlogPostDetailView(generic.DetailView):
    model = BlogPost
    template_name = 'blog/blogpost_detail.html'
    context_object_name = 'blogpost'
    paginate_by = 5

    def dispatch(self, request, *args, **kwargs):
        blogpost = self.get_object()
        if not blogpost.is_published and request.user != blogpost.author:
            raise Http404("This post does not exist.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        username = self.kwargs.get('username')
        blogpost = get_object_or_404(BlogPost, pk=pk, author__username=username)
        return blogpost

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = Comment.objects.filter(blogpost=self.object, is_published=True).order_by('-created_at')
        paginator = Paginator(comments, self.paginate_by)
        page = self.request.GET.get('page')
        comments = paginator.get_page(page)
        context['comments'] = comments
        return context


class BlogPostUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = BlogPost
    fields = ['title', 'text']
    template_name = 'blog/blogpost_update.html'
    success_url = reverse_lazy('home')
    success_message = 'The publication was updated!'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != self.get_object().author:
            raise PermissionDenied("You do not have permission to update this blog post.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        username = self.kwargs.get('username')
        blogpost = get_object_or_404(BlogPost, pk=pk, author__username=username)
        return blogpost

    def form_valid(self, form):
        text = form.cleaned_data.get('text')
        if text:
            form.instance.short_description = text[:50] + '...' if len(text) > 50 else text
        if 'publish' in self.request.POST:
            form.instance.is_published = True
        return super().form_valid(form)


class CommentCreateView(SuccessMessageMixin, generic.CreateView):
    model = Comment
    fields = ['username', 'text']
    template_name = 'blog/comment_create.html'
    success_url = reverse_lazy('home')
    success_message = 'Successfully sent a comment on moderation!'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(BlogPost, pk=self.kwargs['pk'], author__username=self.kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        blogpost = get_object_or_404(BlogPost, pk=self.kwargs['pk'], author__username=self.kwargs['username'])
        form.instance.blogpost = blogpost
        form.instance.save()

        scheme = self.request.scheme
        current_site = get_current_site(self.request)
        url_for_user = reverse("blogpost_detail", args=[blogpost.author.username, blogpost.pk])
        absolute_url_post = f'{scheme}://{current_site.domain}{url_for_user}'

        url_for_admin = reverse('admin:blog_comment_change', args=[form.instance.pk])
        absolute_url_for_admin = f'{scheme}://{current_site.domain}{url_for_admin}'

        # Email to admin
        subject = 'New comment notification!'
        message = ''
        html_message = f'<a href="{absolute_url_for_admin}">Edit comment</a><br>On <a href="{absolute_url_post}">' \
                       f'this post</a><br>Commentator: {form.instance.username}<br>Comment: {form.instance.text}'
        from_email = settings.NOREPLY_EMAIL
        to_email = [user.email for user in User.objects.filter(is_staff=True)]
        celery_send_mail.apply_async((subject, message, from_email, to_email, html_message))

        # Email to user
        subject = f'New comment on post {blogpost.title}'
        message = ''
        html_message = f'New comment by "{form.instance.username}" on <a href="{absolute_url_post}">this post</a>' \
                       f'<br>Comment: {form.instance.text}<br>Remember, that this comment is not published yet, and ' \
                       f'has to be approved by the administrator'
        from_email = settings.NOREPLY_EMAIL
        to_email = [blogpost.author.email]
        celery_send_mail.apply_async((subject, message, from_email, to_email, html_message))

        return super().form_valid(form)


def contact_us(request):
    data = dict()
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            data['form_is_valid'] = True
            customer_name = form.cleaned_data['name']
            customer_email = form.cleaned_data['email']
            subj = form.cleaned_data['subject']
            mes = form.cleaned_data['text']
            subject = 'New user application!'
            message = f'Name: {customer_name}\nEmail: {customer_email}\nSubject: {subj}\nMessage: {mes}'
            celery_send_mail.apply_async((subject, message, settings.NOREPLY_EMAIL, (settings.CONTACT_EMAIL, )))
        else:
            data['form_is_valid'] = False
    else:
        form = ContactUsForm()
    data['html_form'] = render_to_string('blog/contact_us.html', {'form': form}, request=request)
    return JsonResponse(data)
