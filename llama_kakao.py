import time
import re
import win32con
import win32api
import win32gui
import win32clipboard as clipboard
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 카톡창 이름 (열려있는 상태, 최소화 X, 창 뒤에 숨어있는 비활성화 상태 가능)
kakao_opentalk_name = '카카오톡 방'

# Hugging Face 모델과 토크나이저 불러오기
model_name = "MLP-KTLim/llama-3-Korean-Bllossom-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# 모델의 pad_token_id를 eos_token_id로 설정
model.config.pad_token_id = model.config.eos_token_id


def kakao_sendtext(text):
    win32api.SendMessage(hwndEdit, win32con.WM_SETTEXT, 0, text)
    SendReturn(hwndEdit)


# 엔터 키 전송
def SendReturn(hwnd):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)


def send_ctrl_key_combination(hwnd, key):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)


def get_clipboard_text():
    clipboard.OpenClipboard()
    data = clipboard.GetClipboardData(win32con.CF_TEXT)
    clipboard.CloseClipboard()
    return data.decode('euc-kr')


def main():
    previous_gpt_message = ""
    while True:
        hwndMain = win32gui.FindWindow(None, kakao_opentalk_name)
        hwndListControl = win32gui.FindWindowEx(hwndMain, None, "EVA_VH_ListControl_Dblclk", None)

        if hwndMain == 0 or hwndListControl == 0:
            print("Cannot find the KakaoTalk window or list control.")
            time.sleep(2)
            continue

        # 'Ctrl+A' 누르기
        send_ctrl_key_combination(hwndListControl, ord('A'))
        time.sleep(0.5)
        # 'Ctrl+C' 누르기
        send_ctrl_key_combination(hwndListControl, ord('C'))
        time.sleep(0.5)
        ctext = get_clipboard_text()

        # 채팅 내용에서 텍스트 정리
        ctext = re.sub('.*] ', '', ctext)
        ctext = re.sub('\r', '', ctext)

        # 'gpt'가 포함된 메시지 검색
        if 'llama' in ctext:
            time.sleep(2)
            # 'gpt'로 시작하는 마지막 메시지 찾기
            lines = ctext.split('\n')
            gpt_lines = [line for line in lines if line.lower().startswith('llama')]
            if gpt_lines:
                last_gpt_message = gpt_lines[-1]
                print("pre: " + previous_gpt_message + "\n" + "now: " + last_gpt_message + "\n")
                if last_gpt_message != previous_gpt_message:
                    previous_gpt_message = last_gpt_message

                    ## 프롬프트 설정
                    prompt = "d"
                    ### 여기에 LLM 넣기 (last_gpt_message 삽입)
                    inputs = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True)
                    outputs = model.generate(**inputs, max_length=50, num_return_sequences=1)
                    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

                    print(generated_text)
                    print("텍스트 송신")

                    # SETTEXT_test 메시지 전송
                    text = generated_text
                    kakao_sendtext(text)
        time.sleep(2)


if __name__ == '__main__':
    hwndMain = win32gui.FindWindow(None, kakao_opentalk_name)
    hwndEdit = win32gui.FindWindowEx(hwndMain, None, "RICHEDIT50W", None)  # 클래스 이름이 변경될 수 있습니다
    if hwndMain == 0 or hwndEdit == 0:
        print("Cannot find the KakaoTalk window or edit control.")
    else:
        main()