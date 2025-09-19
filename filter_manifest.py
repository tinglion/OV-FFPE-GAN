#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
过滤GDC manifest文件，保留后缀为.svs的文件，并且以前12个字符作为key的集合至少包含两条数据
"""
import os
import csv
import argparse
from collections import defaultdict


def filter_manifest(input_file, output_file=None):
    """
    过滤manifest文件，保留后缀为.svs且文件名中包含DX或者(BS或TS)的文件，并且以前12个字符作为key的集合至少包含两条数据
    
    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径，默认为None，会在输入文件名基础上添加_filtered后缀
    
    返回:
        处理后的数据行数
    """
    # 如果未指定输出文件，自动生成
    if output_file is None:
        base_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(os.path.dirname(input_file), f"{name_without_ext}_filtered.txt")
    
    # 存储以filename前12个字符为key的数据
    key_data_map = defaultdict(list)
    header = None
    
    # 第一次读取：收集所有后缀为.svs的文件，并按key分组
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        # 获取表头
        header = next(reader)
        
        # 读取数据并过滤
        for row in reader:
            if len(row) < 2:
                continue  # 跳过不完整的行
                
            filename = row[1]
            # 检查文件名是否以.svs结尾
            if filename.lower().endswith('.svs') :
                # 以前12个字符作为key
                key = filename[:12]
                key_data_map[key].append(row)
    
    # 第二次处理：只保留出现次数>=2的key对应的数据
    filtered_rows = []
    for key, rows in key_data_map.items():
        has_DX = False
        has_2S = False
        for row in rows:
            if 'DX' in row[1]:
                has_DX = True
            if 'BS' in row[1] or 'TS' in row[1]:
                has_2S = True
        if has_DX and has_2S:
            filtered_rows.extend(rows)
    
    # 写入结果
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)  # 写入表头
        writer.writerows(filtered_rows)
    
    print(f"✅ 过滤完成！")
    print(f"   输入文件: {input_file}")
    print(f"   输出文件: {output_file}")
    print(f"   保留行数: {len(filtered_rows)}")
    
    return len(filtered_rows)


if __name__ == "__main__":
    # 主程序入口 - 添加命令行参数解析
    parser = argparse.ArgumentParser(description='过滤GDC manifest文件，保留后缀为.svs且文件名中包含DX或者(BS或TS)的文件，并且以前12个字符作为key的集合至少包含两条数据')
    parser.add_argument('-i', '--input', required=True, help='输入的manifest文件路径')
    parser.add_argument('-o', '--output', help='输出的过滤后文件路径，默认在输入文件名基础上添加_filtered后缀')
    
    args = parser.parse_args()
    input_file = args.input
    output_file = args.output
    
    # 转换为绝对路径
    if not os.path.isabs(input_file):
        input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), input_file)
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误：找不到文件 {input_file}")
        exit(1)
    
    # 如果指定了输出文件，确保路径存在
    if output_file and not os.path.isabs(output_file):
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # 执行过滤
    filter_manifest(input_file, output_file)