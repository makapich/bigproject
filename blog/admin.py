from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import BlogPost, Comment


@admin.register(BlogPost)
class BlogPost(admin.ModelAdmin):
    list_display = ['title', 'short_description', 'author', 'created_at', 'is_published']
    search_fields = ['title', 'short_description']
    list_filter = ['created_at', ]
    list_per_page = 20
    readonly_fields = ['author', ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['text', 'username', 'get_blogpost_title', 'created_at', 'is_published']
    search_fields = ['text', 'username', 'blogpost__title']
    list_per_page = 20

    def get_blogpost_title(self, obj):
        url = reverse('admin:blog_blogpost_change', args=[obj.blogpost.id])
        return format_html('<a href="{}">{}</a>', url, obj.blogpost.title)

    get_blogpost_title.admin_order_field = 'blogpost__title'
    get_blogpost_title.short_description = 'Blogpost Title'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['blogpost'].widget.can_add_related = False
        return form
