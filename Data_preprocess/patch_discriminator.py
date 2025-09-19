import os
from natsort import natsorted
import glob
import shutil
import matplotlib.pyplot as plt
import h5py
import argparse


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="Script for preparing dataset by considering patient ID",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--frozen-dir", required=True, type=str, help="input frozen .h5 path"
    )
    parser.add_argument(
        "--ffpe-dir", required=True, type=str, help="input FFPE .h5 path"
    )
    parser.add_argument(
        "--train-thresh", default=0.7, type=float, help="ratio of the training set"
    )
    parser.add_argument(
        "--test-thresh", default=0.1, type=float, help="ratio of the test set"
    )
    parser.add_argument(
        "--output-dir", type=str, help="Directory to prepare the dataset"
    )
    return parser.parse_args()


def collect_case_ids(data_path):
    """
    从数据文件路径中收集病例ID

    Args:
        data_path: 数据文件的路径模式

    Returns:
        包含病例ID的集合
    """
    case_id_list = []
    for image_path in natsorted(glob.glob(data_path)):
        case_id = image_path.split(os.sep)[-1]  # 使用os.sep以适应不同操作系统
        case_id_list.append(
            case_id.split("-")[0]
            + "-"
            + case_id.split("-")[1]
            + "-"
            + case_id.split("-")[2]
        )
    return set(case_id_list)


def split_dataset(case_intersect, train_thresh, test_thresh):
    """
    根据指定比例分割数据集为训练集、验证集和测试集

    Args:
        case_intersect: 病例ID的交集集合
        train_thresh: 训练集比例
        test_thresh: 测试集比例

    Returns:
        包含训练集、验证集和测试集ID的元组
    """
    n_train = len(case_intersect) * train_thresh
    n_test = len(case_intersect) * test_thresh
    print(
        f"len(case_intersect)={len(case_intersect)} n_train={n_train} n_test={n_test}"
    )

    set_divider = 0
    train_id = []
    val_id = []
    test_id = []
    for m, case_id in enumerate(case_intersect):
        if set_divider <= n_train:
            train_id.append(case_id)
        elif n_train < set_divider <= n_train + n_test:
            test_id.append(case_id)
        else:
            val_id.append(case_id)
        set_divider += 1
    print(f"train_id: {train_id}")
    print(f"val_id: {val_id}")
    print(f"test_id: {test_id}")

    return train_id, val_id, test_id


def process_and_save_data(
    file_path_pattern, train_id, val_id, test_id, output_dir, suffix
):
    """
    处理数据文件并将其保存到相应的输出目录

    Args:
        file_path_pattern: 数据文件的路径模式
        train_id: 训练集病例ID列表
        val_id: 验证集病例ID列表
        test_id: 测试集病例ID列表
        output_dir: 输出目录路径
        suffix: 输出文件夹后缀（"A"或"B"）
    """
    # 创建输出目录
    train_output = os.path.join(output_dir, f"train{suffix}")
    os.makedirs(train_output, exist_ok=True)
    val_output = os.path.join(output_dir, f"val{suffix}")
    os.makedirs(val_output, exist_ok=True)
    test_output = os.path.join(output_dir, f"test{suffix}")
    os.makedirs(test_output, exist_ok=True)

    for file in natsorted(glob.glob(file_path_pattern)):
        case_id = file.split(os.sep)[-1]  # 使用os.sep以适应不同操作系统
        png_cntr = 0

        case_id_segs = case_id.split("-")
        case_id3 = f"{case_id_segs[0]}-{case_id_segs[1]}-{case_id_segs[2]}"

        if case_id3 in train_id:
            output_path = train_output
        elif case_id3 in val_id:
            output_path = val_output
        elif case_id3 in test_id:
            output_path = test_output
        else:
            continue  # 如果病例ID不在任何集合中，则跳过

        hdf = h5py.File(file)
        for i in list(hdf["imgs"]):
            plt.imsave(f"{output_path}/{case_id}.{png_cntr}.png", i)
            png_cntr += 1


def main():
    """
    主函数，协调整个数据处理流程
    """
    # 解析命令行参数
    args = parse_arguments()

    # 构建文件路径
    frozen_path = os.path.join(args.frozen_dir, "*.h5")
    ffpe_path = os.path.join(args.ffpe_dir, "*.h5")

    # 收集病例ID并找出交集
    case_unique = collect_case_ids(frozen_path)
    case_unique2 = collect_case_ids(ffpe_path)
    case_intersect = case_unique.intersection(case_unique2)

    # 分割数据集
    train_id, val_id, test_id = split_dataset(
        case_intersect, args.train_thresh, args.test_thresh
    )

    # 处理并保存FFPE数据到*B文件夹
    print("Processing FFPE data...")
    process_and_save_data(ffpe_path, train_id, val_id, test_id, args.output_dir, "B")

    # 处理并保存frozen数据到*A文件夹
    print("Processing frozen data...")
    process_and_save_data(frozen_path, train_id, val_id, test_id, args.output_dir, "A")


if __name__ == "__main__":
    main()
