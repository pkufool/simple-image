import os
import json
import requests
import streamlit as st
from PIL import Image
from pathlib import Path
from datetime import datetime
#from logto import LogtoClient, LogtoConfig
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "images"
API_URL = os.getenv("API_URL", "http://localhost:8000")

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

#logto_config = LogtoConfig(
#    endpoint=os.getenv("LOGTO_ENDPOINT"),
#    app_id=os.getenv("LOGTO_APP_ID"),
#    app_secret=os.getenv("LOGTO_APP_SECRET"),
#    redirect_uri=os.getenv("LOGTO_REDIRECT_URI"),
#)
#logto_client = LogtoClient(logto_config)

def login():
    st.subheader("请登录以继续")
    
    # 检查是否有回调参数
    if "code" in st.query_params and "state" in st.query_params:
        try:
            # 完成登录流程
            token_response = logto_client.handle_callback(
                code=st.query_params["code"],
                state=st.query_params["state"]
            )
            
            # 解析ID Token获取用户信息
            id_token = token_response["id_token"]
            user_info = jwt.get_unverified_claims(id_token)
            
            # 保存用户信息到会话状态
            st.session_state["logged_in"] = True
            st.session_state["user"] = {
                "id": user_info.get("sub"),
                "username": user_info.get("username") or user_info.get("email").split("@")[0],
                "email": user_info.get("email"),
                "token": token_response
            }
            
            # 在后端创建/更新用户
            create_user_in_backend(st.session_state["user"])
            
            # 清除查询参数并刷新
            st.query_params.clear()
            st.success("登录成功！")
            st.rerun()
            
        except Exception as e:
            st.error(f"登录失败: {str(e)}")
            st.query_params.clear()
    
    # 显示登录按钮
    authorization_url = logto_client.sign_in_uri()
    st.markdown(f"[点击登录]({authorization_url})", unsafe_allow_html=True)

# 在后端创建用户
def create_user_in_backend(user):
    try:
        response = requests.post(
            f"{API_URL}/users/",
            json={
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        )
        if not response.ok:
            st.warning("用户信息同步失败")
    except Exception as e:
        st.warning(f"用户信息同步出错: {str(e)}")


def handle_file_change(max_num, max_size):
    if "upload_res" in st.session_state:
        st.session_state["upload_res"] = []
    uploaded_files = st.session_state.get(st.session_state["uploader_key"])
    count = 0
    for idx, uploaded_file in enumerate(uploaded_files):
        file_size = uploaded_file.size / (1024 * 1024)  # in MB
        p_key = f"preview_{idx}"
        if p_key not in st.session_state:
            st.session_state[p_key] = False
        if count >= max_num:
            st.error(f"最多上传{max_num}图片")
            continue
        if file_size > max_size:
            st.error(f"{file.name} 超过大小限制（{max_size}MB）")
        else:
            st.session_state[p_key] = True
            count += 1

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = "uploader_1"

# 上传图片
def upload_image():
    st.file_uploader(
        "选择图片",
        accept_multiple_files=True,
        type=["jpg", "JPG", "JPEG", "jpeg", "png", "PNG", "gif"],
        label_visibility="hidden",
        key=st.session_state["uploader_key"],
        on_change=lambda : handle_file_change(max_num=5, max_size=5)
    )
    
    upload_count = 0
    uploaded_files = st.session_state.get(st.session_state["uploader_key"])
    for idx, uploaded_file in enumerate(uploaded_files):
        p_key = f"preview_{idx}"
        if not st.session_state[p_key]:
            continue
        upload_count += 1
        # 显示预览
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        col1.image(image, width=350)
        col2.caption(f"文件名: {uploaded_file.name}")
        col2.multiselect("选择标签", [], accept_new_options=True, key=f"tags_{idx}")
        
    if upload_count > 0:
        if st.button("上传图片", width="stretch", type="primary"):
            success_count = 0
            for idx, uploaded_file in enumerate(uploaded_files):
                p_key = f"preview_{idx}"
                if not st.session_state[p_key]:
                    continue
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getbuffer(),
                            uploaded_file.type
                        )
                    }
                    data = {
                        "user_id": 1,
                        "tags": [],
                    }

                    response = requests.post(
                        f"{API_URL}/upload",
                        files=files,
                        data={"data" : json.dumps(data)},
                    )

                    res = response.json()
                    if "upload_res" not in st.session_state:
                        st.session_state["upload_res"] = []

                    if response.status_code == 200:
                        st.session_state["upload_res"].append(res)
                        p_key = f"preview_{idx}"
                        st.session_state[p_key] = False
                        success_count += 1
                except Exception as e:
                    st.error(f"发生错误: {str(e)}")

            if success_count == upload_count:
                st.session_state["uploader_key"] = f"uploader_{hash(st.session_state['uploader_key'])}"
            st.rerun()

    if "upload_res" in st.session_state and st.session_state["upload_res"]:
        for res in st.session_state["upload_res"]:
            col1, col2 = st.columns([1, 1])
            col1.markdown(f"![{res['filename']}]({res['url']})")

            col2.caption(f"文件名: {res['filename']}")
            col2.caption(f"Tags : a, b,c")
            col2.markdown(f"[{res['url']}]({res['url']})")


# 查看用户图片
def view_user_images():
    st.subheader("我的图片库")
    
    try:
        response = requests.get(
            f"{API_URL}/user-images/{st.session_state['user']['id']}"
        )
        
        if response.status_code == 200:
            images_data = response.json()
            
            if not images_data:
                st.info("您还没有上传任何图片")
                return
            
            # 显示图片列表
            for img in images_data:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    image_path = IMAGES_DIR / f"{img['id']}.{img['file_extension']}"
                    if image_path.exists():
                        image = Image.open(image_path)
                        st.image(image, width=150)
                
                with col2:
                    # 计算节省的空间
                    size_saved = img['original_size'] - img['compressed_size']
                    size_saved_percent = (size_saved / img['original_size']) * 100 if img['original_size'] > 0 else 0
                    
                    st.write(f"**文件名**: {img['filename']}")
                    st.write(f"**上传时间**: {datetime.fromisoformat(img['upload_time'][:-1]).strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**标签**: {', '.join(img['tags'])}" if img['tags'] else "**标签**: 无")
                    st.write(f"**访问链接**: `{API_URL}/image/{img['id']}`")
                    st.write(f"**存储空间**: 原始 {format_size(img['original_size'])} → 压缩 {format_size(img['compressed_size'])} "
                             f"(节省 {format_size(size_saved)}，{size_saved_percent:.1f}%)")
                    
                    # 标签更新
                    new_tags = st.text_input(
                        "修改标签（用逗号分隔）",
                        value=", ".join(img['tags']),
                        key=f"tags_{img['id']}"
                    )
                    
                    # 操作按钮
                    col_update, col_delete = st.columns(2)
                    with col_update:
                        if st.button("更新标签", key=f"update_{img['id']}"):
                            new_tag_list = [tag.strip() for tag in new_tags.split(",")] if new_tags else []
                            update_response = requests.put(
                                f"{API_URL}/update-tags/{img['id']}",
                                json={"tags": new_tag_list},
                                params={"user_id": st.session_state["user"]["id"]}
                            )
                            if update_response.status_code == 200:
                                st.success("标签已更新")
                                st.rerun()
                            else:
                                st.error(f"更新失败: {update_response.text}")
                    
                    with col_delete:
                        if st.button("删除图片", key=f"delete_{img['id']}"):
                            if st.checkbox("确认删除", key=f"confirm_{img['id']}"):
                                delete_response = requests.delete(
                                    f"{API_URL}/delete-image/{img['id']}",
                                    params={"user_id": st.session_state["user"]["id"]}
                                )
                                if delete_response.status_code == 200:
                                    st.success("图片已删除")
                                    st.rerun()
                                else:
                                    st.error(f"删除失败: {delete_response.text}")
            
        else:
            st.error(f"获取图片列表失败: {response.text}")
    except Exception as e:
        st.error(f"发生错误: {str(e)}")

# 工具函数：格式化文件大小
def format_size(bytes, decimals=2):
    """将字节数格式化为人类可读的单位"""
    units = ['B', 'KB', 'MB', 'GB']
    size = float(bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    return f"{size:.{decimals}f} {unit}"

def main():
    st.title("简单图床")
    
    # 初始化会话状态
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    
    # 登录状态检查
    if False and not st.session_state["logged_in"]:
        login()
    else:
        # 显示用户信息
        # st.sidebar.write(f"登录用户: {st.session_state['user']['username']}")
        # st.sidebar.write(f"邮箱: {st.session_state['user']['email']}")
        
        # 登出按钮
        # if st.sidebar.button("登出"):
            # # 清除会话状态
            # st.session_state["logged_in"] = False
            # st.session_state["user"] = None
            # st.rerun()
        
        # 导航菜单
        menu = ["上传图片", "我的图片"]
        choice = st.sidebar.selectbox("菜单", menu)
        
        if choice == "上传图片":
            upload_image()
        elif choice == "我的图片":
            view_user_images()

if __name__ == "__main__":
    main()
