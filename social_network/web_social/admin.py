from django.contrib import admin
from .models import Post
# Register your models here.
class ShowPost(admin.ModelAdmin):
    fields = ('author', 'content','created_at','group','privacy')

admin.site.register(Post,ShowPost)
