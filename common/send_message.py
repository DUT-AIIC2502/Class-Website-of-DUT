import time
from pywinauto import Application, Desktop
import pyperclip


def diagnosis():
    """
    获取诊断信息
    """
    # 诊断脚本
    # 使用 backend="uia" 和 title_re="QQ" 进行模糊匹配
    qq_windows = Desktop(backend="uia").windows(title_re="QQ")

    if qq_windows:
        print(f"成功找到 {len(qq_windows)} 个与QQ相关的窗口：")
        for i, window in enumerate(qq_windows):
            # 打印窗口的序号、精确标题和类名
            print(f"  窗口 {i}:")
            print(f"    标题: '{window.window_text()}'")
            print(f"    类名: {window.class_name()}")
            print("-" * 20)
    else:
        print("没有找到任何标题中包含 'QQ' 的窗口。")
        print("请确保QQ主面板已打开，并且没有被其他窗口完全遮挡。")

    # --- 请将 'QQ - 我的昵称' 替换为你在上一步中找到的精确标题 ---
    EXACT_QQ_WINDOW_TITLE = 'QQ'

    try:
        app = Application(backend="uia").connect(title_re=EXACT_QQ_WINDOW_TITLE)
        qq_main_window = app.window(title_re=EXACT_QQ_WINDOW_TITLE)
        qq_main_window.set_focus()

        print(f"--- 成功连接到 QQ 主窗口: '{EXACT_QQ_WINDOW_TITLE}' ---")
        print("正在打印其控件信息，请查找搜索框...")
        print("-" * 50)

        qq_main_window.print_control_identifiers(depth=None, filename=None)

    except Exception as e:
        print(f"诊断脚本出错: {e}")
        print(f"请确保QQ主面板已打开，并且窗口标题与你设置的 '{EXACT_QQ_WINDOW_TITLE}' 完全一致。")


def send_qq_message(contact_name: str, message: str, qq_window_title="QQ"):
    """
    使用 pywinauto 向指定 QQ 联系人发送消息。

    :param contact_name: 联系人的备注名或昵称。
    :param message: 要发送的消息内容。
    :param qq_window_title: QQ 主窗口的标题（通常是“QQ”或“QQ - 你的昵称”）。
    """

    """尝试从托盘中恢复QQ"""
    if 1 == 1:
        pass

    """步骤 1: 连接到已运行的 QQ"""
    if 1 == 1:
        print(f"正在尝试连接到 QQ...")
        # 使用 backend="uia" 以支持现代 UI 控件
        app = Application(backend="uia").connect(title=f"{qq_window_title}")
        # qq_main = app.window(class_name="TXGuiFoundation")
        qq_main = app.window(title=f"{qq_window_title}")

        print("等待 QQ 窗口变为可见...")
        qq_main.wait('visible', timeout=20)
        print("QQ 窗口已可见。")

        # 确保 QQ 窗口可见
        if not qq_main.is_visible():
            qq_main.restore()  # 从最小化状态恢复
        qq_main.set_focus()
        time.sleep(0.5)  # 等待窗口激活

    """步骤 2: 定位搜索框并搜索联系人"""
    if 1 == 1:
        print(f"正在搜索联系人: {contact_name}")

        # 定位 ComboBox 控件
        search_combo = qq_main.child_window(title_re="搜索", control_type="ComboBox")

        # 清空输入框
        # search_combo.type_keys("^a{BACKSPACE}")  # Ctrl+A, then Backspace

        # 在 ComboBox 的输入框中直接输入文本
        search_combo.type_keys(contact_name)
        time.sleep(0.1)

    """步骤 3: 智能定位并打开聊天窗口"""
    if 1 == 1:
        print(f"正在打开与 {contact_name} 的聊天窗口...")

        # 定位第一个搜索结果 ListItem
        first_result = qq_main.child_window(
            title_re=".*来自:.*",
            control_type="ListItem"
        )

        # 如果找到了 first_result，就点击它
        if first_result:
            first_result.click_input()
            time.sleep(0.1)  # 等待聊天窗口打开

    """步骤 4: 在聊天窗口中发送消息"""
    if 1 == 1:
        # 1. 定位「消息输入框容器」：Dialog - 'Rich Text Editor'
        if 1 == 1:
            print(f"定位输入框容器（Rich Text Editor）...")

            # 定位输入框
            input_dialog = qq_main.child_window(
                title="Rich Text Editor",
                control_type="Window"
            )

            # 验证容器是否存在（避免窗口未加载）
            if not input_dialog.exists():
                print(f"错误：未找到输入框容器「Rich Text Editor」（可能聊天窗口未打开）")
                return False

            # 点击输入框
            input_dialog.set_focus()
            time.sleep(0.1)

        # 2. 定位「实际消息输入框」：Edit
        if 1 == 1:
            print(f"定位消息输入框（Edit控件）...")
            input_box = input_dialog.child_window(
                title=contact_name,  # 输入框title=聊天窗口名称（如“智创2502学习群”）
                control_type="Edit"
            )
            if not input_box.exists():
                print(f"错误：在「Rich Text Editor」中未找到输入框（title应为{contact_name}）")
                return False

        # 3. 向输入框输入消息（用剪贴板避免中文乱码）
        if 1 == 1:
            # 清空输入框
            input_box.type_keys("^a{BACKSPACE}")  # Ctrl+A, then Backspace

            print(f"正在输入消息：{message}")
            input_box.click_input()  # 激活输入框（确保光标在输入框内）
            time.sleep(0.1)
            # 用pyperclip处理中文（避免直接type_keys导致的编码问题）
            pyperclip.copy(message)
            input_box.type_keys("^v")  # Ctrl+V 粘贴消息
            time.sleep(0.1)  # 等待消息粘贴完成

        # 4. 发送消息，通常是按回车
        if 1 == 1:
            input_box.type_keys("{ENTER}")
            print("消息发送成功！\n")