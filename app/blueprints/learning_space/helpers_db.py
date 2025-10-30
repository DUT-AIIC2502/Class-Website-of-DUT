from ext import db
from models import StudyBook


def get_all_books() -> list:
    """
    获取所有学习书籍的列表
    """
    books = []

    categories = ["数学", ]
    
    for category in categories:
        retrieved_books = StudyBook.query.filter_by(category=category, is_published=True).order_by(StudyBook.display_order).all()
        books_list = [category, []]
        for book in retrieved_books:
            books_list[1].append({
                'slug': book.slug,
                'title': book.title,
            })
        books.append(books_list)

    print(books)

    return books