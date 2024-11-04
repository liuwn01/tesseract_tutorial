from collections import defaultdict
import json
import random
import os
import shutil
import datetime

FILE_PREFIX = "GB18030"

#text2image --fonts_dir ./fonts --list_available_fonts --fontconfig_tmpdir ./fonts
FONT_MAPPINT = {
    "simsunb.ttf": "SimSun-ExtB",
    "simsun.ttc": "SimSun",
    "arial.ttf": "Arial",
    "msyh.ttc": "Microsoft YaHei",
    "monbaiti.ttf": "Mongolian Baiti",
    "himalaya.ttf": "Microsoft Himalaya",
    "msyi.ttf": "Microsoft Yi Baiti",
    "taile.ttf": "Microsoft Tai Le",
    "ntailu.ttf": "Microsoft New Tai Lue",
    "seguisym.ttf": "Segoe UI Symbol",
    "micross.ttf": "Microsoft Sans Serif",
}

def Generate_Font_Char_Mapping_Table():
    with open("./tmp/prepare/CharFontMapping.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    result = defaultdict(list)
    for key, value in data.items():
        result[value].append(key)

    result = dict(result)

    with open("./tmp/prepare/grouped_Font_datas.json", "w", encoding="utf-8") as output_file:
        json.dump(result, output_file, ensure_ascii=False, indent=4)

def Loaddatas():
    grouped_Font_datas=None
    exception_strs=None
    with open("./tmp/prepare/grouped_Font_datas.json", "r", encoding="utf-8") as file:
        grouped_Font_datas = json.load(file)

    with open("./tmp/prepare/exception_strs.json", "r", encoding="utf-8") as file:
        exception_strs = json.load(file)
    return grouped_Font_datas, exception_strs

def generate_font_txt(grouped_Font_datas, exception_strs, number_of_generated, random_str_min=15, random_str_max=50, outputFolder="./txt_output"):
    excluded_chars = set()
    for item in exception_strs:
        excluded_chars.update(item["exceptionstrs"])

    generated_strings = {}

    if os.path.exists(outputFolder):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        shutil.rmtree(outputFolder)
        #shutil.move(outputFolder, f"{outputFolder}_{timestamp}")
    os.makedirs(outputFolder, exist_ok=True)

    for key, chars in grouped_Font_datas.items():
        filtered_chars = [char for char in chars if char not in excluded_chars]

        if not filtered_chars:
            print(f"所有字符在 {key} 中都被排除，无法生成字符串。")
            continue

        generated_list = []
        for _ in range(number_of_generated):
            length = random.randint(random_str_min, random_str_max)
            generated_str = ''.join(random.choice(filtered_chars) for _ in range(length))
            generated_list.append(generated_str)

        generated_strings[key] = generated_list
        filename = os.path.abspath(f'{outputFolder}/{FILE_PREFIX}_[{key}].txt')
        with open(filename, 'w', encoding='utf-8') as f:
            for item in generated_list:
                f.write(item + '\n')
        print(f"{filename} generated。")

def generate_font_txt_withexceptionchars(grouped_Font_datas, exception_strs, number_of_generated, random_str_min=15, random_str_max=50, outputFolder="./txt_output"):
    excluded_chars = set()
    for item in exception_strs:
        excluded_chars.update(item["exceptionstrs"])

    for exception in exception_strs:
        tesseract_font = exception["tesseract_font"]
        image_char = exception["image_char"]
        gt_char = exception["gt_char"]

        if tesseract_font in grouped_Font_datas:
            result = {
                "exceptionInfo": exception,
                "txt": []
            }
            font_chars = grouped_Font_datas[tesseract_font]

            filtered_chars = [char for char in font_chars if char not in excluded_chars and char not in gt_char]

            if image_char not in filtered_chars:
                filtered_chars.append(image_char)

            if not filtered_chars:
                print(f"所有字符在 {tesseract_font} 中都被排除，无法生成字符串。")
                continue

            generated_list = result["txt"]
            for _ in range(number_of_generated):
                length = random.randint(random_str_min, random_str_max)
                generated_str = ''.join(random.choice(filtered_chars) for _ in range(length))
                generated_list.append(generated_str)

            # 将结果保存到文件中
            filename = os.path.abspath(f'{outputFolder}/{FILE_PREFIX}_[{tesseract_font}]_Ex.json')  # f'GB_{tesseract_font}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"{filename} generated。")

def Generate_txt(number_of_lines_generated, outputFolder):
    Generate_Font_Char_Mapping_Table()
    grouped_Font_datas, exception_strs = Loaddatas()
    generate_font_txt(grouped_Font_datas, exception_strs, number_of_lines_generated, outputFolder=outputFolder)
    generate_font_txt_withexceptionchars(grouped_Font_datas, exception_strs, number_of_lines_generated, outputFolder=outputFolder)

#generate intermediate data
number_of_lines_generated = 2
outputFolder = "./tmp/txt_output"
Generate_txt(number_of_lines_generated, outputFolder)

#
output_directory = f'tesstrain/data/{FILE_PREFIX}-ground-truth'
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

############################################

import re

FILE_PREFIX = "GB18030"
outputFolder = "./tmp/txt_output"
output_directory = f'tesstrain/data/{FILE_PREFIX}-ground-truth'

cmds = []
for filename in os.listdir(outputFolder):
    file_path = os.path.join(outputFolder, filename)
    if filename.endswith(".txt"):
        # 提取文件名中的值
        match = re.search(f"{FILE_PREFIX}_\[(.*?)\]\.txt", filename)
        if match:
            font_name = match.group(1)

            with open(file_path, 'r', encoding='utf-8') as f:
                # 去掉换行符和回车，将内容存入字典中
                # lines = [line.strip() for line in f if line.strip()]
                line_count = 0
                for line in f:
                    cleaned_line = line.strip()
                    if cleaned_line:  # 如果该行不为空
                        gt_txt_file_name = f"{output_directory}/{FILE_PREFIX}.{font_name}.{line_count}.gt.txt"
                        with open(gt_txt_file_name, 'w', encoding='utf-8') as outfile:
                            outfile.write(cleaned_line)
                            cmds.append(
                                [
                                    'text2image',
                                    f'--font={FONT_MAPPINT[font_name]}',
                                    f'--text={gt_txt_file_name}',  # 替换为实际的文本变量
                                    f'--outputbase={output_directory}/{FILE_PREFIX}.{font_name}.{line_count}',
                                    # 替换为实际的目录和文件名变量
                                    '--max_pages=1',
                                    '--strip_unrenderable_words',
                                    '--leading=32',
                                    '--xsize=3600',
                                    '--ysize=480',
                                    '--char_spacing=1.0',
                                    '--exposure=0',
                                    '--unicharset_file=langdata/eng.unicharset',
                                    '--fonts_dir=./fonts',
                                    f'--fontconfig_tmpdir=./fonts'
                                ]
                            )#{os.path.abspath("./fonts")}
                            line_count += 1
        else:
            raise Exception(f"unknown filename:{filename}")


import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
# 定义一个函数来执行命令
def run_command(command):
    # 使用 subprocess.run 执行命令，并返回结果
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

# 使用 ThreadPoolExecutor 来并行执行命令
max_workers = 4  # 最大同时执行的命令数
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 提交所有命令到线程池
    futures = {executor.submit(run_command, cmd): cmd for cmd in cmds}

    # 获取每个命令的执行结果
    for future in as_completed(futures):
        cmd = futures[future]
        cmd = ' '.join(cmd)
        try:
            stdout, stderr = future.result()
            print(f"Command: {cmd}\nOutput: {stdout}\nErrors: {stderr}\n")
        except Exception as e:
            print(f"Command {cmd} generated an exception: {e}")