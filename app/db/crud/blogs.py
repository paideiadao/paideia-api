import uuid
from fastapi import status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from db.models.blogs import Blog
from db.schemas.blog import CreateOrUpdateBlog

#################################
### CRUD OPERATIONS FOR BLOGS ###
#################################


def get_blogs(
    db: Session,
    search_string: str = "",
    highlights_only: bool = False,
    education_only: bool = False,
    limit: int = 100
):
    db_blogs = db.query(Blog).filter(
        Blog.name.ilike(f"%{search_string}%")
    ).order_by(Blog.date.desc()).limit(limit).all()
    filtered_blogs = []
    for blog in db_blogs:
        ok = True
        if highlights_only and not ("add_to_highlights" in blog.additional_details and blog.additional_details["add_to_highlights"]):
            ok = False
        if education_only and not ("add_to_education_page" in blog.additional_details and blog.additional_details["add_to_education_page"]):
            ok = False
        if ok:
            filtered_blogs.append(blog)
    return filtered_blogs


def get_blog(db: Session, link: str):
    db_blog = db.query(Blog).filter(Blog.link == link).first()
    if not db_blog:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="blog not found")
    return db_blog


def get_blog_by_id(db: Session, id: uuid.UUID):
    db_blog = db.query(Blog).filter(Blog.id == id).first()
    return db_blog


def generate_blog_link(name: str):
    return ''.join(name.lower().split())


def create_blog(db: Session, blog: CreateOrUpdateBlog):
    db_blog = Blog(
        name=blog.name,
        link=generate_blog_link(blog.name),
        img_url=blog.img_url,
        description=blog.description,
        content=blog.content,
        category=blog.category,
        additional_details=blog.additional_details.dict()
    )
    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog


def edit_blog(db: Session, id: uuid.UUID, blog: CreateOrUpdateBlog):
    db_blog = get_blog_by_id(db, id)
    if not db_blog:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="blog not found")

    update_data = blog.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("addtional_details",):
            value = value.dict()
        setattr(db_blog, key, value)

    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog


def delete_blog(db: Session, id: uuid.UUID):
    db_blog = get_blog_by_id(db, id)
    if not db_blog:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="blog not found")
    db.delete(db_blog)
    db.commit()
    return db_blog
