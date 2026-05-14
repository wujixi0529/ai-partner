import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

# 设置页面配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

#保存会话信息
def save_session():
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,
            "character": st.session_state.character,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        #如果sessions目录不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        #保存会话数据
        with open("sessions/%s.json" % st.session_state.current_session, "w",encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

#生成会话标识
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#加载所有的会话列表信息
def load_sessions():
    sessions_list = []
    #加载sessions目录下的所有文件
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for file in file_list:
            if file.endswith(".json"):
                sessions_list.append(file[:-5])
    sessions_list.sort(reverse=True)
    return sessions_list

#加载指定会话数据
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error("加载会话失败")

#删除指定会话
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
    except Exception as e:
        st.error("删除会话失败")

# 大标题
st.title("AI智能伴侣")

st.logo("resources/logo.png")

# 系统提示词
system_prompt = """
                你叫 %s ，现在是用户的真实伴侣，请完全带入伴侣角色。
                规则：
                    1.每次只回1条消息
                    2.禁止任何场景或状态描述性文字
                    3.匹配用户的语言
                    4.回复简短，像微信聊天一样
                    5.用符合伴侣性格的方式对话
                    6.回复的内容，要充分体现伴侣的性格特征
                伴侣性格：
                    - %s
                你必须严格遵守以上规则来回复用户
            """

# 初始化聊天信息
if 'messages' not in st.session_state:
    st.session_state.messages = []
# 昵称
if 'nick_name' not in st.session_state:
    st.session_state.nick_name = "小喜"
# 性格
if 'character' not in st.session_state:
    st.session_state.character = "粘人的小狗型的小男孩"
# 会话标识
if 'current_session' not in st.session_state:
    datetime_now = generate_session_name()
    st.session_state.current_session = datetime_now

st.text(f"会话名称：{st.session_state.current_session}")
# 展示聊天信息,遍历列表
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
    # if message["role"] == "user":
    #     st.chat_message("user").write(message["content"])
    # else:
    #     st.chat_message("assistant").write(message["content"])


client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

# 左侧侧边栏
with st.sidebar:
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话",width="stretch",icon="✏️"):
        if st.session_state.messages:  # 判断聊天消息是否为空
            # 1.保存当前会话信息
            save_session()

            #2.创建新的会话
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            # 重新运行当前页面
            st.rerun()

    #会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 =  st.columns([4,1])
        with col1:
            #加载会话信息
            if st.button(session, width="stretch",icon="📂", key=f"load_{session}",type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
        with col2:
            #删除会话信息
            if st.button("", width="stretch",icon="❌️",key=f"delete_{session}"):
                delete_session(session)
                if session == st.session_state.current_session:
                    st.session_state.messages = []
                    st.session_state.current_session = generate_session_name()
                st.rerun()

    #分割线
    st.divider()

    st.subheader("伴侣信息")
    nick_name = st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    character = st.text_area("性格",placeholder="请输入性格",value=st.session_state.character)
    if character:
        st.session_state.character = character


# 输入框
prompt = st.chat_input("请输入你的问题")
if prompt:
    st.chat_message("user").write(prompt)
    print("-->调用ai大模型，提示词", prompt)
    # 保存用户提示词
    st.session_state.messages.append({"role": "user" , "content": prompt})

    # 调用ai大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name,st.session_state.character)},
            #解决历史会话记忆
            *st.session_state.messages
        ],
        stream=True
        # reasoning_effort="high",
        # extra_body={"thinking": {"type": "enabled"}}
    )

    # 输出大模型返回的结果(非流式输出)
    # st.chat_message("assistant").write(response.choices[0].message.content)
    # print("<--ai大模型返回的结果：",response.choices[0].message.content)

    # 输出大模型返回的结果(流式输出)
    response_message = st.empty() # 创建一个空的组件,用于显示大模型返回的结果
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    # 保存大模型返回值
    st.session_state.messages.append({"role": "assistant" , "content": full_response})

    #保存会话信息
    save_session()