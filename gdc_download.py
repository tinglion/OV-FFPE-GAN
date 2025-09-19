import requests
import json
import subprocess
import time
import os
import csv


def load_manifest(filename="temp/gdc_manifest.LUSC.txt"):
    data = []
    with open(filename, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # 获取表头字段名
        fieldnames = reader.fieldnames
        print(f"📋 表头字段名: {fieldnames}")
        # 读取每行数据
        for row in reader:
            if row["filename"].find(".svs") >= 0:
                data.append(row)
    print(f"✅ 成功加载 {len(data)} 行数据")
    return data, {row["filename"][0:23]: row for row in data}


# 配置
GDC_API = "https://api.gdc.cancer.gov/files"
headers = {"Content-Type": "application/json"}

# 适配Windows路径
# GDC_CLIENT = os.path.join("F:", "bingli", "gdc-client.exe")
GDC_CLIENT = "/mnt/f/bingli/gdc-client"


def mk_filters(filename):
    return {
        "op": "and",
        "content": [
            # {
            #     "op": "like",
            #     "content": {
            #         "field": "files.file_name",
            #         "value": filename
            #     }
            # },
            {
                "op": "in",
                "content": {
                    "field": "cases.submitter_id",
                    "value": [
                        filename[0:12],
                        # "TCGA-43-3920",
                    ],
                },
            },
            {
                "op": "=",
                "content": {"field": "files.data_type", "value": "Slide Image"},
            },
        ],
    }


def fetch_info(fn_list, fn_targe, limit=2):
    file_map = {}
    if os.path.exists(fn_targe):
        with open(fn_targe, "r") as fp:
            file_map = json.load(fp)
            fp.close()

    # 读取文件名列表
    with open(fn_list, "r") as f:
        src_names = [line.strip() for line in f if line.strip()]
        f.close()
    for i, filename in enumerate(src_names):
        if limit and i >= limit:
            break

        print(f"\n🔍 查询{i}: {filename}")
        if filename in file_map and file_map[filename].get("id"):
            continue

        try:
            # 构建更精确的过滤器
            filters = mk_filters(filename)

            # 如果精确匹配没有结果，再尝试模糊匹配
            params = {
                "filters": json.dumps(filters),
                "fields": "file_id,file_name,data_type,submitter_id",
                "format": "json",
                "size": 100,
            }

            response = requests.get(GDC_API, headers=headers, params=params)
            print(response.text)

            if response.status_code != 200:
                print(f"❌ API 请求失败: {response.status_code}, {filename}")
            else:
                data = response.json()

                hits = data.get("data", {}).get("hits", [])
                if hits:
                    print(f"hits={len(hits)}")
                    for hit in hits:
                        file_id = hit["id"]
                        real_name = hit["file_name"]
                        # TCGA-43-3920-01Z-00-DX1
                        if real_name.find(filename[0:23]) >= 0:
                            file_map[filename] = {
                                "id": file_id,
                                "file_name": real_name,
                            }
                            print(f"✅ 找到: {file_id} -> {real_name}")
                            break
            if not file_map.get(filename):
                file_map[filename] = {"id": "", "file_name": ""}

            # 每次保存，以防失联
            with open(fn_targe, "w") as fp:
                json.dump(file_map, fp, indent=2)
                fp.close()
            time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print(f"ERROR {e} i={i} filename={filename}")
    return file_map


def save_manifest(file_map, fn_output):
    os.makedirs(os.path.dirname(fn_output), exist_ok=True)
    with open(fn_output, "w") as f:
        f.write("id\n")
        for src in file_map:
            f.write(f"{file_map[src]['id']}\n")
    print(f"\n📝 生成下载清单: {fn_output}")


def gdc_download(outdir, fn_output):
    os.makedirs(outdir, exist_ok=True)
    print("\n⬇️ 开始下载...")
    # 检查GDC客户端是否存在
    if os.path.exists(GDC_CLIENT):
        cmd = [GDC_CLIENT, "download", "-m", fn_output, "-d", outdir]
        # 在Windows上运行命令
        try:
            subprocess.run(cmd, check=True)
            print("✅ 下载完成!")
        except subprocess.CalledProcessError as e:
            print(f"❌ 下载失败: {e}")
    else:
        print(f"❌ 找不到GDC客户端: {GDC_CLIENT}")


if __name__ == "__main__":
    # file_map = fetch_info(fn_list="docs/lung_trainB_slide_nos.txt")
    # save_manifest(file_map)
    # gdc_download("temp/trainB")

    fn_list = "temp/lung_trainA.txt"
    fn_targe = "temp/lung_trainA_slide_nos.json"
    fn_output = "temp/gdc_manifest.2S.txt"
    fn_download = "temp/trainA"

    file_map = fetch_info(fn_list, fn_targe, limit=2)
    save_manifest(file_map, fn_output)
    gdc_download(fn_download, fn_output)

    pass
