"""
Django QuerySet Completion Test Cases

This file contains all test cases for django.nvim completion features.
Open this file in Neovim and test autocomplete at each marked position.

Models used:
- Comment (blog app): post, author, parent, content, is_approved, moderation_status, replies, etc.
- Post (blog app): title, author, category, tags, status, etc.
- User (auth app): username, email, first_name, last_name, etc.
"""

from blog.models import Comment, Post
from django.contrib.auth.models import User

# =============================================================================
# 1. FILTER-STYLE METHODS (fields + lookups + all relations)
# =============================================================================


def test_filter():
    # Test 1.1: Basic field completion
    # Expected: all fields (content, author, post, is_approved, etc.) + lookups
    Comment.objects.filter()
    #                      ^ cursor here

    # Test 1.2: Field with lookups
    # Expected: content field + content__exact, content__icontains, etc.
    # Comment.objects.filter(content)
    #                              ^ type 'content' then trigger completion

    # Test 1.3: Lookup completion (after __)
    # Expected: exact, isnull, in, iexact, contains, icontains, startswith, etc.
    # Comment.objects.filter(content__)
    #                                ^ type 'content__' then trigger completion

    # Test 1.4: Relation traversal
    # Expected: User model fields (username, email, first_name, etc.)
    # Comment.objects.filter(author__)
    #                               ^ type 'author__' then trigger completion

    # Test 1.5: Deep relation traversal with lookup
    # Expected: CharField lookups (exact, iexact, contains, etc.)
    # Comment.objects.filter(author__username__)
    #                                         ^ type then trigger completion


def test_exclude():
    # Test 1.6: Same as filter
    # Expected: all fields + lookups + relations
    Comment.objects.exclude()
    #                       ^ cursor here


def test_get():
    # Test 1.7: Same as filter
    # Expected: all fields + lookups + relations
    Comment.objects.get()
    #                   ^ cursor here


def test_get_or_create():
    # Test 1.8: Same as filter
    # Expected: all fields + lookups + relations
    Comment.objects.get_or_create()
    #                             ^ cursor here


def test_update_or_create():
    # Test 1.9: Same as filter
    # Expected: all fields + lookups + relations
    Comment.objects.update_or_create()
    #                                ^ cursor here


# =============================================================================
# 2. CREATE/UPDATE METHODS (fields only, NO lookups, NO relations)
# =============================================================================


def test_create():
    # Test 2.1: Fields only
    # Expected: content, is_approved, moderation_status, author_id, post_id, etc.
    # NOT expected: content__exact, author__username
    Comment.objects.create()
    #                      ^ cursor here


def test_update():
    # Test 2.2: Fields only
    # Expected: content, is_approved, moderation_status, etc.
    # NOT expected: content__exact, author__username
    Comment.objects.filter(id=1).update()
    #                                   ^ cursor here


# =============================================================================
# 3. FIELD-ONLY METHODS (fields + relations, NO lookups)
# =============================================================================


def test_values():
    # Test 3.1: Fields + relations, no lookups
    # Expected: content, author, post, is_approved, etc.
    # NOT expected: content__exact
    Comment.objects.values()
    #                      ^ cursor here

    # Test 3.2: Relation traversal allowed (inside quotes)
    # Expected: User fields (username, email, etc.)
    Comment.objects.values("author__first_name")
    #                                ^ type 'author__' then trigger


def test_values_list():
    # Test 3.3: Same as values
    # Expected: fields + relations, no lookups
    Comment.objects.values_list()
    #                           ^ cursor here


def test_only():
    # Test 3.4: Fields + FK/O2O only (no M2M, no reverse relations)
    # Expected: content, author, post, parent, is_approved, etc.
    # NOT expected: replies (ManyToOneRel)
    Comment.objects.only()
    #                    ^ cursor here


def test_defer():
    # Test 3.5: Same as only
    # Expected: fields + FK/O2O only
    Comment.objects.defer()
    #                     ^ cursor here


# =============================================================================
# 4. RELATIONS-ONLY METHODS (NO regular fields)
# =============================================================================


def test_select_related():
    # Test 4.1: FK/O2O relations only (inside quotes)
    # Expected: author, post, parent
    # NOT expected: content, replies, tags
    Comment.objects.select_related("author")
    #                               ^ type inside quotes

    # Test 4.2: Nested relation traversal
    # Expected: Post's FK/O2O relations (author, category)
    Comment.objects.select_related("post__author")
    #                                    ^ type 'post__' then trigger


def test_prefetch_related():
    # Test 4.3: All relation types (FK, O2O, M2M, reverse)
    # Expected: author, post, parent, replies
    # NOT expected: content, is_approved
    Comment.objects.prefetch_related("")
    #                                 ^ type inside quotes


# =============================================================================
# 5. ORDER/ANNOTATION METHODS (fields + relations, NO lookups)
# =============================================================================


def test_order_by():
    # Test 5.1: Fields + relations, no lookups
    # Expected: content, author, post, created_at, etc.
    # NOT expected: content__exact
    Comment.objects.order_by()
    #                        ^ cursor here

    # Test 5.2: Relation traversal (inside quotes)
    # Expected: User fields
    Comment.objects.order_by("author__username")
    #                                 ^ type 'author__' then trigger


def test_annotate():
    # Test 5.3: Fields + relations for F() expressions
    # Expected: content, author, post, etc.
    Comment.objects.annotate()
    #                        ^ cursor here


def test_aggregate():
    # Test 5.4: Same as annotate
    # Expected: fields + relations
    Comment.objects.aggregate()
    #                         ^ cursor here


# =============================================================================
# 6. COMPLEX CHAINED QUERIES
# =============================================================================


def test_chained_queries():
    # Test 6.1: filter -> select_related
    Comment.objects.filter(is_approved=True).select_related("author")
    #                                                        ^ cursor here

    # Test 6.2: filter -> values
    Comment.objects.filter(is_approved=True).values("")
    #                                               ^ cursor here

    # Test 6.3: filter -> order_by
    Comment.objects.filter(is_approved=True).order_by()
    #                                                 ^ cursor here


# =============================================================================
# 7. DIFFERENT MODELS
# =============================================================================


def test_post_model():
    # Test 7.1: Post model filter
    # Expected: title, author, category, tags, status, content, etc.
    Post.objects.filter()
    #                   ^ cursor here

    # Test 7.2: Post -> author traversal
    # Expected: User fields
    # Post.objects.filter(author__)
    #                            ^ type 'author__' then trigger

    # Test 7.3: Post select_related
    # Expected: author, category (FK relations)
    Post.objects.select_related("author")
    #                            ^ cursor here

    # Test 7.4: Post prefetch_related
    # Expected: author, category, tags, comments (including M2M and reverse)
    Post.objects.prefetch_related("comments")
    #                              ^ cursor here


def test_user_model():
    # Test 7.5: User model filter
    User.objects.filter()
    #                   ^ cursor here

    # Test 7.6: User -> reverse relation traversal
    # Expected: blog_posts fields (Post model)
    # User.objects.filter(blog_posts__)
    #                                ^ type 'blog_posts__' then trigger


# =============================================================================
# 8. EDGE CASES
# =============================================================================


def test_edge_cases():
    # Test 8.1: Multiple arguments - completion after comma
    Comment.objects.filter(is_approved=True, content="test")
    #                                      ^ position cursor after comma, before content

    # Test 8.2: Partial typing
    # Comment.objects.filter(cont)
    #                            ^ type 'cont' - should filter to content*

    # Test 8.3: After relation with partial
    # Comment.objects.filter(author__user)
    #                                    ^ type 'author__user' - should filter to username*

    # Test 8.4: _id fields - should show proper documentation
    Comment.objects.filter(author_id=1)
    #                               ^ should show: author_id = models.AutoField() -> User.pk


# =============================================================================
# SUMMARY OF EXPECTED BEHAVIORS
# =============================================================================
"""
Method              | Fields | Lookups | FK/O2O | M2M | Reverse
--------------------|--------|---------|--------|-----|--------
filter              |   Y    |    Y    |   Y    |  Y  |    Y
exclude             |   Y    |    Y    |   Y    |  Y  |    Y
get                 |   Y    |    Y    |   Y    |  Y  |    Y
get_or_create       |   Y    |    Y    |   Y    |  Y  |    Y
update_or_create    |   Y    |    Y    |   Y    |  Y  |    Y
create              |   Y    |    N    |   N    |  N  |    N
update              |   Y    |    N    |   N    |  N  |    N
values              |   Y    |    N    |   Y    |  Y  |    Y
values_list         |   Y    |    N    |   Y    |  Y  |    Y
only                |   Y    |    N    |   Y    |  N  |    N
defer               |   Y    |    N    |   Y    |  N  |    N
select_related      |   N    |    N    |   Y    |  N  |    N
prefetch_related    |   N    |    N    |   Y    |  Y  |    Y
order_by            |   Y    |    N    |   Y    |  Y  |    Y
annotate            |   Y    |    N    |   Y    |  Y  |    Y
aggregate           |   Y    |    N    |   Y    |  Y  |    Y
"""
