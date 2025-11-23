import uuid

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy import select

from app.db import Post as PostModel, create_db_and_tables, get_async_session

from sqlalchemy.ext.asyncio import AsyncSession

from contextlib import asynccontextmanager

from app.schemas import Post
from app.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

text_posts = {
    1: {"title": "new title", "content": "new content"},
    2: {"title": "cool title", "content": "cool content"},
}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...),
                      caption: str = Form("caption"),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    post = PostModel(
        caption=caption,
        url="dummy url",
        file_type="photo",
        file_name=file.filename,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(PostModel).order_by(PostModel.created_at.desc()))
    # posts = result.scalars().all()
    posts = [row[0] for row in result.all()]
    posts_data = []
    for post in posts:
        posts_data.append({
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {"posts": posts_data}


@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(PostModel).where(PostModel.uuid == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        await session.delete(post)
        await session.commit()

        return {"success": True, "message": "Deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/hello-world")
async def hello_world():
    return {"message": "Hello World"}


@app.get("/posts")
async def get_all_posts():
    return text_posts


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return text_posts.get(post_id)


@app.post("/posts")
# async def create_post(post: Post)->Post:
async def create_post(post: Post):
    # new_post = Post(title=post.title, content=post.content)
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post

    return new_post
